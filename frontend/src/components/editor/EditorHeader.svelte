<script>
  import { listRevisions, startRevisionHistory, restoreRevision } from "../../lib/api/revisions.js";
  import { listDrafts, createDraft, renameDraft, deleteDraft, switchDraft } from "../../lib/api/drafts.js";
  import { getIndexingStatus } from "../../lib/api/indexing.js";
  import { onDestroy } from "svelte";

  // Shared state stays in the parent so menus and keyboard shortcuts stay coordinated.
  let {
    id,
    projectId,
    title,
    editor,
    onback,
    menuItems,
    runMenu,
    save,
    icon,
    onRestore,
    onDraftChange,
    saveTick,
    saving = false,
    canSave = true,
    menuOpen = $bindable(null),
    open = $bindable(false),
  } = $props();

  let revisions = $state([]);
  let revisionsLoading = $state(false);
  let revisionsError = $state("");
  let historyStarted = $state(true);
  let restoringId = $state(null);
  let confirmId = $state(null);

  let drafts = $state([]);
  let draftsLoading = $state(false);
  let draftsError = $state("");
  let draftsStarted = $state(true);
  let draftBusy = $state(false);
  let newDraftName = $state("");
  let creating = $state(false);
  let renamingName = $state(null);
  let renameValue = $state("");
  let deleteConfirm = $state(null);

  let revisionMessage = $state("");
  let messageInput = $state(null);

  function toggleSaveMenu() {
    if (menuOpen === "save") {
      menuOpen = null;
    } else {
      menuOpen = "save";
      // Focus after the panel renders.
      queueMicrotask(() => messageInput?.focus());
      // The draft name shown in the panel is only known once drafts are loaded.
      if (drafts.length === 0) loadDrafts();
    }
  }

  async function submitSave(e) {
    e.preventDefault();
    const message = revisionMessage.trim();
    menuOpen = null;
    revisionMessage = "";
    await save(message || undefined);
  }

  // Indexing status: reflects the assistant index for this manuscript's current content.
  // Saving re-queues indexing (see OnManuscriptSaved on the backend), which runs
  // synchronously by default, but polling covers real async job queues too.
  /** @type {{status: string, chunk_count: number, searchable: boolean} | null} */
  let indexStatus = $state(null);
  let indexError = $state("");
  let indexPollHandle = null;

  const INDEX_LABELS = {
    not_indexed: "Not indexed",
    pending: "Indexing queued…",
    indexing: "Indexing…",
    indexed: "Indexed",
    failed: "Indexing failed",
  };

  async function loadIndexStatus() {
    try {
      indexStatus = await getIndexingStatus(projectId, id);
      indexError = "";
    } catch (e) {
      indexError = e.message;
    }
    schedulePoll();
  }

  // Poll while a background job could still be running; stop once settled.
  function schedulePoll() {
    clearTimeout(indexPollHandle);
    if (indexStatus && (indexStatus.status === "pending" || indexStatus.status === "indexing")) {
      indexPollHandle = setTimeout(loadIndexStatus, 2000);
    }
  }

  onDestroy(() => clearTimeout(indexPollHandle));

  loadIndexStatus();

  // Re-check status whenever the parent reports a save (saveTick increments).
  let lastSaveTick = 0;
  $effect(() => {
    const tick = saveTick ?? 0;
    if (tick !== lastSaveTick) {
      lastSaveTick = tick;
      loadIndexStatus();
    }
  });

  let currentDraft = $derived(drafts.find((d) => d.is_current)?.name ?? "main");

  async function loadDrafts() {
    draftsLoading = true;
    draftsError = "";
    try {
      drafts = await listDrafts(projectId, id);
      draftsStarted = true;
    } catch (e) {
      if (/not found/i.test(e.message)) {
        draftsStarted = false;
        drafts = [];
      } else {
        draftsError = e.message;
      }
    } finally {
      draftsLoading = false;
    }
  }

  // Run a draft mutation, then refresh the list; surfaces errors in the panel.
  async function runDraftAction(fn, { reloadContent = false } = {}) {
    draftBusy = true;
    draftsError = "";
    try {
      await fn();
      await loadDrafts();
      if (reloadContent) onDraftChange?.();
      return true;
    } catch (e) {
      draftsError = e.message;
      return false;
    } finally {
      draftBusy = false;
    }
  }

  const startDraftTracking = () =>
    runDraftAction(() => startRevisionHistory(projectId, id));

  const doSwitch = (name) =>
    runDraftAction(() => switchDraft(projectId, id, name), { reloadContent: true });

  async function doCreate() {
    const name = newDraftName.trim();
    if (!name) return;
    if (await runDraftAction(() => createDraft(projectId, id, name))) {
      newDraftName = "";
      creating = false;
    }
  }

  async function doRename(name) {
    const next = renameValue.trim();
    if (!next) return;
    if (await runDraftAction(() => renameDraft(projectId, id, name, next))) renamingName = null;
  }

  async function doDelete(name) {
    if (await runDraftAction(() => deleteDraft(projectId, id, name))) deleteConfirm = null;
  }

  function toggleDrafts() {
    if (menuOpen === "drafts") {
      menuOpen = null;
    } else {
      menuOpen = "drafts";
      creating = false;
      renamingName = null;
      deleteConfirm = null;
      loadDrafts();
    }
  }

  async function loadRevisions() {
    revisionsLoading = true;
    revisionsError = "";
    try {
      revisions = await listRevisions(projectId, id);
      historyStarted = true;
    } catch (e) {
      if (/not found/i.test(e.message)) {
        historyStarted = false;
        revisions = [];
      } else {
        revisionsError = e.message;
      }
    } finally {
      revisionsLoading = false;
    }
  }

  async function startHistory() {
    revisionsLoading = true;
    revisionsError = "";
    try {
      await startRevisionHistory(projectId, id);
      await loadRevisions();
    } catch (e) {
      revisionsError = e.message;
    } finally {
      revisionsLoading = false;
    }
  }

  async function doRestore(revisionId) {
    restoringId = revisionId;
    try {
      await restoreRevision(projectId, id, revisionId);
      confirmId = null;
      menuOpen = null;
      onRestore?.();
    } catch (e) {
      revisionsError = e.message;
    } finally {
      restoringId = null;
    }
  }

  function toggleRevisions() {
    if (menuOpen === "revisions") {
      menuOpen = null;
    } else {
      menuOpen = "revisions";
      confirmId = null;
      revisionsError = "";
      loadRevisions();
    }
  }
</script>

  <header class="editor-header">
    <div class="document-controls">
      <button type="button" class="back-button" onclick={onback} title="Back to Project Dashboard" aria-label="Back to Project Dashboard">{@render icon('back')}</button>
      <!-- TODO(API): MERGE
           Connect source/target draft IDs, conflict handling, and server confirmation.
           Enable only after a real merge handler is implemented. -->
      <button type="button" class="pill" disabled title="Merge is not implemented">{@render icon('merge', 12)} Merge</button>
      <!-- ACTIVE API: Drafts panel lists, creates, renames, deletes and switches drafts.
           The manuscript content is the latest revision of the current draft. -->
      <div class="dropdown">
        <button type="button" class="pill branch" onclick={toggleDrafts} aria-expanded={menuOpen === 'drafts'}>{@render icon('branch', 12)} {currentDraft} {@render icon('chevron', 10)}</button>
        {#if menuOpen === 'drafts'}
          <div class="dropdown-panel draft-panel" aria-label="Drafts">
            {#if draftsLoading && drafts.length === 0}
              <p>Loading drafts…</p>
            {:else if !draftsStarted}
              <p>Draft tracking hasn't started for this manuscript.</p>
              <button type="button" class="primary" disabled={draftBusy} onclick={startDraftTracking}>Start tracking</button>
            {:else}
              <strong>Drafts</strong>
              {#if draftsError}<p class="draft-error">{draftsError}</p>{/if}
              {#each drafts as d (d.name)}
                <div class="draft-item">
                  {#if renamingName === d.name}
                    <form class="draft-form" onsubmit={(e) => { e.preventDefault(); doRename(d.name); }}>
                      <input aria-label="New draft name" maxlength="64" bind:value={renameValue} />
                      <button type="submit" disabled={draftBusy || !renameValue.trim()}>Save</button>
                      <button type="button" onclick={() => (renamingName = null)}>Cancel</button>
                    </form>
                  {:else}
                    <button type="button" class="draft-name" disabled={draftBusy || d.is_current} onclick={() => doSwitch(d.name)} title={d.is_current ? 'Current draft' : `Switch to ${d.name}`}>
                      <span>{d.name}{d.is_current ? ' ✓' : ''}</span><small>{d.revision_count} rev.</small>
                    </button>
                    {#if d.name !== 'main'}
                      {#if deleteConfirm === d.name}
                        <div class="draft-actions">
                          <span>Delete?</span>
                          <button type="button" onclick={() => (deleteConfirm = null)}>No</button>
                          <button type="button" class="primary" disabled={draftBusy} onclick={() => doDelete(d.name)}>Yes</button>
                        </div>
                      {:else}
                        <div class="draft-actions">
                          <button type="button" disabled={draftBusy} onclick={() => { renamingName = d.name; renameValue = d.name; }}>Rename</button>
                          <button type="button" disabled={draftBusy || d.is_current} title={d.is_current ? 'Switch to another draft first' : ''} onclick={() => (deleteConfirm = d.name)}>Delete</button>
                        </div>
                      {/if}
                    {/if}
                  {/if}
                </div>
              {/each}
              {#if creating}
                <form class="draft-form" onsubmit={(e) => { e.preventDefault(); doCreate(); }}>
                  <input aria-label="Draft name" placeholder="Draft name" maxlength="64" bind:value={newDraftName} />
                  <button type="submit" disabled={draftBusy || !newDraftName.trim()}>Create</button>
                  <button type="button" onclick={() => { creating = false; newDraftName = ''; }}>Cancel</button>
                </form>
              {:else}
                <button type="button" onclick={() => (creating = true)}>Create draft</button>
              {/if}
            {/if}
          </div>
        {/if}
      </div>
      <div class="document-meta">
        <div class="title-row"><h2 class="name" title={String(title)}>{title}</h2><span class="save-status"><span>•</span> Manual save</span>
          <span class="index-status {indexStatus?.status ?? 'unknown'}" role="status" aria-live="polite"
            title={indexError || (indexStatus?.status === 'failed' ? 'The last indexing attempt failed. Save again to retry.' : 'Whether the assistant can search this manuscript')}>
            {#if indexError}Index status unavailable
            {:else if !indexStatus}Checking index…
            {:else}{INDEX_LABELS[indexStatus.status]}{#if indexStatus.status === 'indexed'} · {indexStatus.chunk_count} chunk{indexStatus.chunk_count === 1 ? '' : 's'}{/if}{/if}
          </span></div>
        <nav class="menu-bar" aria-label="Document menus">
          {#each ['File', 'Edit', 'View', 'Insert', 'Format', 'Tools', 'Help'] as menu}
            <div class="dropdown"><button type="button" onclick={() => menuOpen = menuOpen === menu ? null : menu} aria-expanded={menuOpen === menu}>{menu}</button>
              {#if menuOpen === menu}<div class="dropdown-panel" aria-label={`${menu} actions`}>
                {#each menuItems[menu] as item}<button type="button" disabled={item.disabled || !editor} onclick={() => runMenu(item.action)}>{item.label}{#if item.disabled}<small>Unavailable</small>{/if}</button>{/each}
              </div>{/if}</div>
          {/each}
        </nav>
      </div>
    </div>
    <div class="header-actions">
      <!-- ACTIVE API: Save calls the existing save() function. Indexing status is shown
           next to the title (GET .../indexing-status). Per-chunk progress is not exposed. -->
      <div class="dropdown save-split">
        <button type="button" class="pill primary save-main" onclick={() => save()} disabled={!editor || saving || !canSave} title={canSave ? '' : 'Save is unavailable until the manuscript has loaded'}>{@render icon('save', 12)} {saving ? 'Saving…' : 'Save'}</button>
        <button type="button" class="pill primary save-toggle" onclick={toggleSaveMenu} disabled={!editor || saving || !canSave} aria-label="Save with revision message" aria-haspopup="true" aria-expanded={menuOpen === 'save'}>{@render icon('chevron', 10)}</button>
        {#if menuOpen === 'save'}
          <form class="dropdown-panel save-panel" aria-label="Save options" onsubmit={submitSave}>
            <label for="revision-message"><strong>Revision message</strong></label>
            <input id="revision-message" bind:this={messageInput} bind:value={revisionMessage} maxlength="256" placeholder="Manual save" autocomplete="off" />
            <small class="save-hint">Saved to draft "{currentDraft}". Leave blank to use "Manual save".</small>
            <button type="submit" class="primary">{@render icon('save', 12)} Save with message</button>
          </form>
        {/if}
      </div>
      <!-- ACTIVE API: Revisions panel lists committed revisions and restores them.
           History auto-starts on first save (see editor.svelte); the panel offers
           a manual start button if history hasn't been initialised yet. -->
      <div class="dropdown">
        <button type="button" class="pill" class:active={menuOpen === 'revisions'} onclick={toggleRevisions} aria-expanded={menuOpen === 'revisions'}>{@render icon('history', 12)} Revisions</button>
        {#if menuOpen === 'revisions'}
          <div class="dropdown-panel revisions-panel" aria-label="Revision history">
            {#if revisionsLoading}
              <p class="revisions-status">Loading revisions…</p>
            {:else if revisionsError}
              <p class="revisions-status error">{revisionsError}</p>
              <button type="button" onclick={loadRevisions}>Retry</button>
            {:else if !historyStarted}
              <p class="revisions-status">Revision tracking hasn't started for this manuscript.</p>
              <button type="button" class="primary" onclick={startHistory}>Start tracking</button>
            {:else if revisions.length === 0}
              <p class="revisions-status">No revisions yet. Save the document to create one.</p>
            {:else}
              <strong>Revision history</strong>
              {#each revisions as rev}
                <div class="revision-item">
                  <div class="revision-meta">
                    <span class="revision-message">{rev.message}</span>
                    <span class="revision-date">{new Date(rev.created_at).toLocaleString()}</span>
                  </div>
                  {#if confirmId === rev.id}
                    <div class="revision-confirm">
                      <span>Restore this revision?</span>
                      <div class="revision-confirm-actions">
                        <button type="button" onclick={() => (confirmId = null)}>Cancel</button>
                        <button type="button" class="primary" disabled={restoringId === rev.id} onclick={() => doRestore(rev.id)}>
                          {restoringId === rev.id ? 'Restoring…' : 'Confirm'}
                        </button>
                      </div>
                    </div>
                  {:else}
                    <button type="button" onclick={() => (confirmId = rev.id)}>Restore</button>
                  {/if}
                </div>
              {/each}
            {/if}
          </div>
        {/if}
      </div>
      <button type="button" class="pill" class:active={open} onclick={() => (open = !open)} aria-expanded={open} aria-controls="theseus-chat">{@render icon('panel', 12)} Chat</button>
    </div>
  </header>
<style>
  .editor-header, .editor-header * { box-sizing: border-box; }
  button { font: inherit; color: inherit; margin: 0; }
  button { display: inline-flex; align-items: center; justify-content: center; gap: 6px; cursor: pointer; line-height: 1.3; }
  button:disabled { cursor: default; opacity: 1; -webkit-text-fill-color: currentColor; }
  button:not(:disabled):hover { background: #e9ede9; }
  button:focus-visible { outline: 2px solid var(--green); outline-offset: 2px; }
  .editor-header { background: var(--surface); border-bottom: 1px solid #e2e6e2; padding: 6px 16px; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; }
  .document-controls, .header-actions { display: flex; align-items: center; gap: 8px; min-width: 0; }
  .document-controls { flex: 1; }
  .header-actions { flex-shrink: 0; gap: 10px; }
  .back-button { width: 28px; height: 28px; border-radius: 50%; border: 1px solid var(--border); background: #f2f4f2; flex-shrink: 0; padding: 0; }
  .pill { border: 1px solid var(--border); border-radius: 999px; background: #f4f6f4; padding: 5px 13px; font-size: 10.5px; font-weight: 600; white-space: nowrap; }
  .branch { border-color: var(--accent-border); }
  .primary, .active { background: var(--green); color: white; border-color: var(--green); }
  .primary:not(:disabled):hover, .active:not(:disabled):hover { background: var(--accent-hover); }
  .document-meta { margin-left: 6px; min-width: 0; }
  .title-row { display: flex; align-items: center; gap: 8px; }
  .name { font-size: 12.5px; font-weight: 700; color: var(--text-h); margin: 0; line-height: 1.2; max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .save-status { font-size: 9px; color: var(--text-muted); white-space: nowrap; font-family: var(--mono); }
  .save-split { display: inline-flex; }
  .save-main { border-top-right-radius: 0; border-bottom-right-radius: 0; }
  .save-toggle { border-top-left-radius: 0; border-bottom-left-radius: 0; border-left-color: #ffffff55; padding: 5px 9px; }
  .save-panel { left: auto; right: 0; width: 250px; display: flex; flex-direction: column; gap: 6px; padding: 10px; }
  .save-panel input { font-size: 11px; padding: 6px 8px; border: 1px solid var(--border); border-radius: 5px; }
  .save-panel .primary { justify-content: center; width: 100%; background: var(--green); color: white; }
  .save-hint { font-size: 9px; color: var(--text-muted); }
  .save-status span { color: var(--green); margin-right: 4px; }
  .index-status { font-size: 9px; font-family: var(--mono); white-space: nowrap; padding: 1px 7px; border-radius: 999px; border: 1px solid var(--border); color: var(--text-muted); }
  .index-status.indexed { color: var(--green); border-color: var(--accent-border); }
  .index-status.pending, .index-status.indexing { color: #8a6d00; border-color: #e6d58a; }
  .index-status.failed { color: #c0392b; border-color: #e6b0aa; }
  .menu-bar { display: flex; gap: 2px; margin-left: -6px; margin-top: 2px; }
  .menu-bar button { border: 0; background: transparent; padding: 2px 7px; border-radius: 4px; font-size: 11px; font-weight: 400; color: #202124; }
  .dropdown { position: relative; }
  .dropdown-panel { position: absolute; top: calc(100% + 5px); left: 0; z-index: 60; width: 205px; max-width: 80vw; padding: 5px; background: var(--surface); border: 1px solid var(--accent-border); border-radius: 9px; box-shadow: 0 12px 30px #19282226; }
  .dropdown-panel button, .menu-bar .dropdown-panel button { display: flex; justify-content: space-between; width: 100%; padding: 8px; border: 0; border-radius: 5px; background: transparent; text-align: left; font-size: 11px; }
  .dropdown-panel button:disabled { color: #78867f; }.dropdown-panel small { font-size: 8px; }
  .draft-panel { padding: 12px; }.draft-panel p { font-size: 10px; color: var(--text-muted); }
  .draft-panel { width: 260px; }
  .draft-error { color: #c0392b; }
  .draft-item { border-top: 1px solid var(--border); padding: 3px 0; }
  .draft-item:first-of-type { border-top: 0; }
  .draft-name small { color: var(--text-muted); font-size: 9px; }
  .draft-actions { display: flex; align-items: center; justify-content: flex-end; gap: 4px; }
  .draft-actions span { font-size: 10px; color: var(--text-muted); }
  .draft-actions button, .draft-form button { width: auto; padding: 3px 8px; font-size: 10px; border: 1px solid var(--border); }
  .draft-form { display: flex; gap: 4px; align-items: center; margin-top: 4px; }
  .draft-form input { flex: 1; min-width: 0; font-size: 11px; padding: 4px 6px; border: 1px solid var(--border); border-radius: 5px; }
  .menu-bar .dropdown:last-child .dropdown-panel { left: auto; right: 0; }
  .revisions-panel { width: 280px; max-height: 360px; overflow-y: auto; left: auto; right: 0; }
  .revisions-status { font-size: 10px; color: var(--text-muted); margin: 0; }
  .revisions-status.error { color: #c0392b; }
  .revision-item { padding: 6px 4px; border-top: 1px solid var(--border); }
  .revision-item:first-of-type { border-top: 0; }
  .revision-meta { display: flex; flex-direction: column; gap: 2px; margin-bottom: 4px; }
  .revision-message { font-size: 11px; font-weight: 600; color: var(--text-h); }
  .revision-date { font-size: 9px; color: var(--text-muted); font-family: var(--mono); }
  .revision-confirm { margin-top: 4px; }
  .revision-confirm > span { font-size: 10px; color: var(--text-muted); }
  .revision-confirm-actions { display: flex; justify-content: flex-end; gap: 6px; margin-top: 6px; }
  .revision-confirm-actions button { border: 1px solid var(--border); border-radius: 5px; padding: 4px 10px; font-size: 10px; }
  .revision-item > button { border: 0; background: transparent; color: var(--green); font-size: 10px; padding: 2px 0; }
  .revision-item > button:hover { text-decoration: underline; }
  .editor-header { position: relative; z-index: 20; flex-shrink: 0; }

  
  

@media (max-width: 1023px) { .document-controls { flex-wrap: wrap; } .title-row { flex-wrap: wrap; } .header-actions { margin-left: auto; } }

@media (max-width: 560px) { .document-controls { flex: 1 0 100%; width: 100%; } .header-actions { margin-left: 0; } .editor-header { padding: 8px 12px; } .document-meta { flex-basis: 100%; margin: 4px 0 0; } .name { max-width: 240px; } .menu-bar { flex-wrap: wrap; } }
</style>
