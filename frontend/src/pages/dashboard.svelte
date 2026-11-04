<script>
  import { untrack } from "svelte";
  import ManuscriptCard from "../components/dashboard/ManuscriptCard.svelte";
  import SourceLibrary from "../components/dashboard/SourceLibrary.svelte";
  import {
    listManuscripts,
    createManuscript,
    deleteManuscript,
    renameManuscript,
  } from "../lib/api/manuscripts.js";

  /** @type {{ selectedProject: {id: string, name: string} | null, refreshKey?: number, oncount?: (count: number) => void, onselect: (id: string, projectId: string) => void, onback: () => void }} */
  let { selectedProject = null, refreshKey = 0, oncount, onselect, onback } = $props();

  // ── data state ───────────────────────────────────────────────────────────────
  let manuscripts = $state([]);
  let loading = $state(false);
  let error = $state('');
  // True when the list itself failed to load, so "No manuscripts yet" isn't shown.
  let loadFailed = $state(false);

  // Report the current manuscript count so the app header stays in sync after
  // load, create and delete.
  $effect(() => {
    oncount?.(manuscripts.length);
  });

  // ── ui state ─────────────────────────────────────────────────────────────────
  let collabOpen = $state(false);

  // ── create dialog ─────────────────────────────────────────────────────────────
  let createDialog = $state(null);
  let createTitle = $state('');
  let createTemplate = $state(false);
  let createError = $state('');
  let createBusy = $state(false);

  // ── rename dialog ─────────────────────────────────────────────────────────────
  let renameDialog = $state(null);
  let renameTarget = $state(null);
  let renameTitle = $state('');
  let renameError = $state('');
  let renameBusy = $state(false);

  // ── load ──────────────────────────────────────────────────────────────────────
  let requestId = 0;

  function withTimeout(promise, ms = 10000) {
    return Promise.race([
      promise,
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Request timed out.')), ms)
      ),
    ]);
  }

  $effect(() => {
    const id = selectedProject?.id;
    // refreshKey changes each time the user returns from the editor, ensuring
    // the list stays up-to-date after a save without requiring a full remount.
    refreshKey;
    if (id) untrack(() => load(id));
  });

  async function load(projectId) {
    const req = ++requestId;
    loading = true;
    error = '';
    loadFailed = false;
    try {
      const result = await withTimeout(listManuscripts(projectId));
      if (req !== requestId) return;
      manuscripts = result;
    } catch (e) {
      if (req !== requestId) return;
      error = e.message;
      loadFailed = true;
    } finally {
      if (req === requestId) loading = false;
    }
  }

  // ── create ────────────────────────────────────────────────────────────────────
  function openCreateDialog() {
    createTitle = '';
    createTemplate = false;
    createError = '';
    createDialog?.showModal();
  }

  async function handleCreate(event) {
    event.preventDefault();
    const title = createTitle.trim();
    if (!title) { createError = 'Title is required.'; return; }
    createBusy = true;
    createError = '';
    try {
      await createManuscript(selectedProject.id, title, createTemplate);
      createDialog?.close();
      await load(selectedProject.id);
    } catch (e) {
      createError = e.message;
    } finally {
      createBusy = false;
    }
  }

  // ── rename ────────────────────────────────────────────────────────────────────
  function openRenameDialog(doc) {
    renameTarget = doc;
    renameTitle = doc.title;
    renameError = '';
    renameDialog?.showModal();
  }

  async function handleRename(event) {
    event.preventDefault();
    const title = renameTitle.trim();
    if (!title) { renameError = 'Title is required.'; return; }
    renameBusy = true;
    renameError = '';
    try {
      await renameManuscript(selectedProject.id, renameTarget.id, title);
      renameDialog?.close();
      await load(selectedProject.id);
    } catch (e) {
      renameError = e.message;
    } finally {
      renameBusy = false;
    }
  }

  // ── delete ────────────────────────────────────────────────────────────────────
  async function handleDelete(doc) {
    if (!confirm(`Delete "${doc.title}"? This cannot be undone.`)) return;
    error = '';
    try {
      await deleteManuscript(selectedProject.id, doc.id);
      await load(selectedProject.id);
    } catch (e) {
      error = e.message;
    }
  }

  function closeCollab(event) {
    if (!event.target.closest?.('.collab-control')) collabOpen = false;
  }
</script>

<svelte:window
  onclick={closeCollab}
  onkeydown={event => { if (event.key === 'Escape') collabOpen = false; }}
/>

{#snippet icon(name, size = 14)}
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    {#if name === 'document'}<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6M8 13h8M8 17h8"/>
    {:else if name === 'folder'}<path d="M3 7V5a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/>
    {:else if name === 'person'}<circle cx="12" cy="7" r="4"/><path d="M4 21v-2a4 4 0 0 1 4-4h8a4 4 0 0 1 4 4v2"/>
    {:else if name === 'clock'}<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
    {:else if name === 'back'}<path d="M19 12H5m7-7-7 7 7 7"/>
    {:else if name === 'close'}<path d="m6 6 12 12M18 6 6 18"/>
    {:else if name === 'ellipsis'}<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>
    {:else if name === 'edit'}<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4Z"/>
    {:else if name === 'trash'}<path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
    {:else if name === 'books'}<path d="M4 19V6a2 2 0 0 1 2-2h6v15H6a2 2 0 0 1-2-2Z"/><path d="M12 4h4a2 2 0 0 1 2 2v13h-6Z"/><path d="M2 19h20"/>
    {/if}
  </svg>
{/snippet}

<div class="theseus-dashboard">
  <main class="dashboard-content">

    <!-- Breadcrumb -->
    <div class="workspace-breadcrumb">
      <button type="button" onclick={() => onback?.()} title="Back to all projects">
        {@render icon('back')} All Theseus Projects
      </button>
      <span>/</span>
      <span class="workspace-badge">{selectedProject?.name ?? 'YOUR WORKSPACE'}</span>
    </div>

    <!-- Project card -->
    <section class="project-card surface" aria-labelledby="workspace-title">
      <div class="project-copy">
        <h1 id="workspace-title">Research Workspace</h1>
        <p>Organize your manuscripts, review recent updates, and continue writing. Select a manuscript below or create a new document.</p>
      </div>
      <div class="project-actions">
        <button type="button" class="new-button" onclick={openCreateDialog}>
          <span class="plus">+</span> New Manuscript
        </button>
        <div class="collab-control">
          <button
            type="button"
            class="primary-button"
            onclick={() => collabOpen = !collabOpen}
            aria-expanded={collabOpen}
            aria-controls="collab-panel"
          >
            {@render icon('person')} Collab <span class="plus">+</span>
          </button>
          {#if collabOpen}
            <div class="collab-panel" id="collab-panel">
              <div class="popover-heading">
                <strong>Add Members</strong>
                <button type="button" class="icon-button" onclick={() => collabOpen = false} aria-label="Close collaboration panel">
                  {@render icon('close')}
                </button>
              </div>
              <p>Collaboration is not available yet.</p>
              <label>SEARCH MEMBER<input disabled placeholder="Search Account" /></label>
              <button type="button" class="primary-button" disabled>Add +</button>
            </div>
          {/if}
        </div>
      </div>
    </section>

    <!-- Error banner -->
    {#if error}
      <div class="error-banner" role="alert">{error} <button type="button" class="retry" onclick={() => load(selectedProject.id)}>Retry</button></div>
    {/if}

    <!-- Main grid -->
    <div class="dashboard-grid">
      <section aria-labelledby="manuscripts-heading">
        <div class="section-heading">
          <h2 id="manuscripts-heading">{@render icon('document')} Manuscripts ({manuscripts.length})</h2>
          <span>Click to open in editor</span>
        </div>

        <div class="manuscript-list">
          {#if loading}
            <div class="manuscript-skeletons" role="status" aria-label="Loading manuscripts">
              {#each { length: 3 } as _}<div class="skeleton-card"></div>{/each}
            </div>
          {:else}
            {#each manuscripts as doc (doc.id)}
              <ManuscriptCard
                {doc}
                {icon}
                onselect={(id) => onselect?.(id, selectedProject.id, doc.title)}
                onrename={openRenameDialog}
                ondelete={handleDelete}
              />
            {:else}
              {#if !loadFailed}
              <div class="empty-card surface">
                <span class="empty-icon">{@render icon('document', 25)}</span>
                <h3>No manuscripts yet</h3>
                <p>Create your first manuscript to start writing.</p>
                <button type="button" class="primary-button" onclick={openCreateDialog}>+ New Manuscript</button>
              </div>
              {/if}
            {/each}
          {/if}
        </div>
      </section>

      <SourceLibrary {icon} />
    </div>
  </main>
</div>

<!-- Create dialog -->
<dialog bind:this={createDialog} class="input-dialog" aria-labelledby="create-dialog-title">
  <form onsubmit={handleCreate}>
    <h3 id="create-dialog-title">New Manuscript</h3>

    <label>
      Title
      <input
        bind:value={createTitle}
        maxlength="256"
        required
        placeholder="e.g., Chapter 1 Draft"
      />
    </label>

    <label class="checkbox-label">
      <input type="checkbox" bind:checked={createTemplate} />
      Start with thesis template sections
    </label>

    {#if createError}
      <p class="field-error" role="alert">{createError}</p>
    {/if}

    <div class="dialog-actions">
      <button type="button" onclick={() => createDialog?.close()}>Cancel</button>
      <button type="submit" class="primary" disabled={createBusy}>
        {createBusy ? 'Creating…' : 'Create'}
      </button>
    </div>
  </form>
</dialog>

<!-- Rename dialog -->
<dialog bind:this={renameDialog} class="input-dialog" aria-labelledby="rename-dialog-title">
  <form onsubmit={handleRename}>
    <h3 id="rename-dialog-title">Rename Manuscript</h3>

    <label>
      New title
      <input
        bind:value={renameTitle}
        maxlength="256"
        required
        placeholder="Enter a new title"
      />
    </label>

    {#if renameError}
      <p class="field-error" role="alert">{renameError}</p>
    {/if}

    <div class="dialog-actions">
      <button type="button" onclick={() => renameDialog?.close()}>Cancel</button>
      <button type="submit" class="primary" disabled={renameBusy}>
        {renameBusy ? 'Saving…' : 'Rename'}
      </button>
    </div>
  </form>
</dialog>

<style>
  /* Shared fonts and theme come from index.html and app.css. */
  .theseus-dashboard { width: 100%; min-height: calc(100dvh - 48px); flex: 1; color-scheme: light; background: var(--page-background); color: var(--text); font: 11px/1.5 var(--sans); text-align: left; }
  .theseus-dashboard * { box-sizing: border-box; }
  button, input { font: inherit; color: inherit; }
  button { cursor: pointer; }
  button:disabled { cursor: default; opacity: 1; }
  button:focus-visible, input:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }

  .dashboard-content { max-width: 884px; margin: 0 auto; padding: 36px 32px 60px; }
  .workspace-breadcrumb { display: flex; align-items: center; gap: 8px; font-size: 10.5px; color: #5a6760; margin-bottom: 14px; }
  .workspace-breadcrumb button { display: inline-flex; align-items: center; gap: 6px; border: 0; background: none; padding: 0; font-weight: 500; }
  .workspace-badge { font: 600 9.5px var(--mono); padding: 4px 8px; border-radius: 4px; background: #dee5df; color: #2f3b35; }

  .surface { background: var(--surface); border: 1.5px solid transparent; border-radius: 14px; box-shadow: var(--shadow); }
  .project-card { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 28px; margin-bottom: 28px; }
  .project-copy { max-width: 450px; min-width: 0; }
  h1 { font-size: 20px; font-weight: 700; letter-spacing: -.025em; color: var(--text-h); margin: 0 0 8px; }
  .project-copy p { font-size: 10.5px; line-height: 1.6; color: var(--text-muted); margin: 0; }

  .project-actions { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
  .new-button, .primary-button { display: inline-flex; align-items: center; justify-content: center; gap: 6px; font-size: 10.5px; font-weight: 600; border-radius: 7px; padding: 8px 14px; border: 1px solid var(--border); background: #f4f5f3; white-space: nowrap; }
  .new-button:hover { background: #eaece9; }
  .primary-button { background: var(--accent); color: white; border-color: var(--accent); }
  .primary-button:not(:disabled):hover { background: var(--accent-hover); }
  .plus { font-size: 14px; font-weight: 400; line-height: 1; }

  .error-banner { background: #fdf0f0; border: 1px solid #e8b4b4; border-radius: 8px; color: #b94040; font-size: 11px; padding: 10px 14px; margin-bottom: 18px; display: flex; align-items: center; gap: 10px; }
  .error-banner .retry { font-size: 10px; font-weight: 600; color: #b94040; background: transparent; border: 1px solid currentColor; border-radius: 5px; padding: 3px 9px; }
  .manuscript-skeletons { display: flex; flex-direction: column; gap: 10px; }
  .skeleton-card { height: 58px; border-radius: 9px; border: 1px solid #e2e6e2; background: linear-gradient(90deg, #eef1ee 25%, #f6f8f6 37%, #eef1ee 63%); background-size: 400% 100%; animation: shimmer 1.4s ease infinite; }
  @keyframes shimmer { 0% { background-position: 100% 0; } 100% { background-position: 0 0; } }

  .dashboard-grid { display: grid; grid-template-columns: minmax(0, 2fr) minmax(0, 1fr); gap: 24px; align-items: start; }
  .section-heading { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin: 0 2px 12px; }
  h2 { display: flex; align-items: center; gap: 7px; font-size: 10.5px; text-transform: uppercase; letter-spacing: .04em; font-weight: 700; margin: 0; }
  .section-heading > span { font-size: 10px; color: var(--text-muted); }
  .manuscript-list { display: grid; gap: 16px; }
  .empty-icon { display: inline-flex; color: var(--accent-border); margin-bottom: 8px; }
  h3 { margin: 0 0 6px; font-size: 11px; }
  .empty-card { padding: 36px 20px; text-align: center; }
  .empty-card h3 { font-size: 14px; }
  .empty-card p { color: var(--text-muted); margin: 0 0 16px; }

  .collab-control { position: relative; }
  .collab-panel { position: absolute; right: 0; top: calc(100% + 10px); z-index: 30; width: 235px; padding: 14px; border: 1.5px solid var(--accent-border); border-radius: 11px; background: var(--surface); box-shadow: 0 14px 34px #19282238; }
  .popover-heading { display: flex; justify-content: space-between; align-items: center; padding-bottom: 10px; border-bottom: 1px solid #e6eae6; }
  .icon-button { display: flex; border: 0; background: transparent; padding: 2px; }
  .collab-panel p { font-size: 10px; color: var(--text-muted); }
  .collab-panel label { display: grid; gap: 6px; font: 8px var(--mono); color: var(--text-muted); margin-bottom: 10px; }
  .collab-panel input { width: 100%; border: 1px solid var(--border); border-radius: 5px; padding: 8px; background: #f2f4f1; }
  .collab-panel .primary-button:disabled { background: #7c8d84; border-color: #7c8d84; }

  /* Dialogs */
  .input-dialog { width: min(380px, calc(100vw - 32px)); border: 1px solid var(--accent-border); border-radius: 12px; padding: 22px; background: var(--surface); color: var(--text); font: 12px var(--sans); box-shadow: 0 20px 60px #19282233; }
  .input-dialog::backdrop { background: #19282255; }
  .input-dialog h3 { font-size: 14px; margin: 0 0 16px; font-weight: 700; }
  .input-dialog label { display: grid; gap: 6px; margin-bottom: 12px; }
  .input-dialog input:not([type]) { width: 100%; padding: 9px; border: 1px solid #aeb9b3; border-radius: 6px; background: white; color: var(--text); font: inherit; }
  .checkbox-label { display: flex; flex-direction: row; align-items: center; gap: 8px; cursor: pointer; }
  .checkbox-label input[type="checkbox"] { width: 14px; height: 14px; flex-shrink: 0; cursor: pointer; accent-color: var(--accent); }
  .field-error { color: #b94040; font-size: 10.5px; margin: 4px 0 0; }
  .dialog-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 18px; }
  .dialog-actions button { border: 1px solid #aeb9b3; border-radius: 6px; padding: 7px 14px; }
  .dialog-actions .primary { background: var(--accent); color: white; border-color: var(--accent); }
  .dialog-actions .primary:not(:disabled):hover { background: var(--accent-hover); }
  .dialog-actions .primary:disabled { opacity: 0.65; cursor: default; }

  @media(max-width: 767px) { .project-card { flex-direction: column; align-items: flex-start; padding: 24px; } .dashboard-grid { grid-template-columns: 1fr; } .dashboard-content { padding: 28px 16px 40px; } }
  @media(max-width: 420px) { .workspace-breadcrumb { flex-wrap: wrap; } .project-card { padding: 20px; } .section-heading { flex-wrap: wrap; } .project-actions { gap: 8px; } .new-button, .primary-button { padding: 8px 11px; } }
</style>
