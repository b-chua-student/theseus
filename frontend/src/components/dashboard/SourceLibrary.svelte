<script>
  import { listSources, addSource, removeSource, updateSourceMetadata } from '../../lib/api/sources.js';

  import { tick, untrack } from 'svelte';
  import { getTextSource } from '../../lib/api/textSources.js';
  import TextSourceList from '../text-sources/TextSourceList.svelte';
  import TextSourceForm from '../text-sources/TextSourceForm.svelte';

  /** @type {{ icon: Function, projectId?: string }} */
  let { icon, projectId = '' } = $props();

  // ── data ──────────────────────────────────────────────────────────────────────
  /** @type {import('../../lib/api/sources.js').Source[]} */
  let sources = $state([]);
  const tabs = ['Text Sources', 'Source Library'];
  let activeTab = $state(0);

  function navigateTabs(event) {
    const keys = { ArrowLeft: 1 - activeTab, ArrowRight: 1 - activeTab, Home: 0, End: 1 };
    if (!Object.hasOwn(keys, event.key)) return;
    event.preventDefault();
    activeTab = keys[event.key];
    event.currentTarget.parentElement.children[activeTab].focus();
  }
  let loading = $state(false);
  let error = $state('');
  let loadFailed = $state(false);

  // ── add dialog ────────────────────────────────────────────────────────────────
  let addDialog = $state(null);
  let addTitle = $state('');
  let addAuthorsRaw = $state('');
  let addYear = $state('');
  let addFileRef = $state('');
  let addError = $state('');
  let addBusy = $state(false);

  // ── edit dialog ───────────────────────────────────────────────────────────────
  let editDialog = $state(null);
  /** @type {import('../../lib/api/sources.js').Source | null} */
  let editTarget = $state(null);
  let editTitle = $state('');
  let editAuthorsRaw = $state('');
  let editYear = $state('');
  let editError = $state('');
  let editBusy = $state(false);

  // ── text sources ──────────────────────────────────────────────────────────────
  /** 'list' shows the text source list; 'form' shows the create/edit form. */
  let textView = $state('list');
  let textEditing = $state(null);
  let textRefresh = $state(0);
  let textError = $state('');

  let createTextDialog = $state(null);
  async function openTextCreate() {
    textEditing = null;
    textError = '';
    textView = 'create';
    await tick();
    if (textView === 'create') createTextDialog?.showModal();
  }

  async function openTextEdit(summary) {
    textError = '';
    try {
      // The list only carries snippets; the form needs the full content.
      textEditing = await getTextSource(projectId, summary.id);
      textView = 'form';
    } catch (e) {
      textError = e.message;
    }
  }

  function closeTextForm() {
    if (createTextDialog?.open) createTextDialog.close();
    textView = 'list';
    textEditing = null;
  }

  // Switching projects returns to the list; an open edit belongs to the old project.
  let lastProjectId = untrack(() => projectId);
  $effect.pre(() => {
    if (projectId !== lastProjectId) {
      lastProjectId = projectId;
      activeTab = 0;
      textView = 'list';
      textEditing = null;
      textError = '';
    }
  });

  function handleTextSaved() {
    closeTextForm();
    textRefresh += 1;
  }

  // ── load ──────────────────────────────────────────────────────────────────────
  $effect(() => { load(); });

  async function load() {
    loading = true;
    error = '';
    loadFailed = false;
    try {
      // Text sources are listed (with search/filter/paging) by TextSourceList.
      sources = (await listSources()).filter((s) => s.kind !== 'text');
    } catch (e) {
      error = e.message;
      loadFailed = true;
    } finally {
      loading = false;
    }
  }

  // ── add ───────────────────────────────────────────────────────────────────────
  function openAddDialog() {
    addTitle = '';
    addAuthorsRaw = '';
    addYear = '';
    addFileRef = '';
    addError = '';
    addDialog?.showModal();
  }

  async function handleAdd(event) {
    event.preventDefault();
    const title = addTitle.trim();
    const fileRef = addFileRef.trim();
    if (!title) { addError = 'Title is required.'; return; }
    if (!fileRef) { addError = 'File reference is required.'; return; }

    const authors = addAuthorsRaw.split(',').map(a => a.trim()).filter(Boolean);
    const year = addYear ? parseInt(addYear, 10) : null;
    if (addYear && isNaN(year)) { addError = 'Year must be a number.'; return; }

    addBusy = true;
    addError = '';
    try {
      await addSource(title, authors.length ? authors : null, year, fileRef);
      addDialog?.close();
      await load();
    } catch (e) {
      addError = e.message;
    } finally {
      addBusy = false;
    }
  }

  // ── edit ──────────────────────────────────────────────────────────────────────
  function openEditDialog(source) {
    editTarget = source;
    editTitle = source.title;
    editAuthorsRaw = source.authors.join(', ');
    editYear = source.year != null ? String(source.year) : '';
    editError = '';
    editDialog?.showModal();
  }

  async function handleEdit(event) {
    event.preventDefault();
    const title = editTitle.trim();
    if (!title) { editError = 'Title is required.'; return; }

    const authors = editAuthorsRaw.split(',').map(a => a.trim()).filter(Boolean);
    const year = editYear ? parseInt(editYear, 10) : null;
    if (editYear && isNaN(year)) { editError = 'Year must be a number.'; return; }

    editBusy = true;
    editError = '';
    try {
      await updateSourceMetadata(editTarget.id, title, authors, year);
      editDialog?.close();
      await load();
    } catch (e) {
      editError = e.message;
    } finally {
      editBusy = false;
    }
  }

  // ── remove ────────────────────────────────────────────────────────────────────
  async function handleRemove(source) {
    if (!confirm(`Remove "${source.title}"? This cannot be undone.`)) return;
    error = '';
    try {
      await removeSource(source.id);
      await load();
    } catch (e) {
      error = e.message;
    }
  }
</script>

<aside class="source-card surface" aria-label="Research sources">
  {#if projectId}
    <div class="source-tabs" role="tablist" aria-label="Source collections">
      {#each tabs as tab, i (tab)}
        <button type="button" role="tab" id={'source-tab-' + i} aria-controls={'source-panel-' + i}
          aria-selected={activeTab === i} tabindex={activeTab === i ? 0 : -1}
          onclick={() => activeTab = i} onkeydown={navigateTabs}>{tab}</button>
      {/each}
    </div>
  {/if}
  <div id="source-panel-1" role={projectId ? 'tabpanel' : undefined} aria-labelledby={projectId ? 'source-tab-1' : undefined} hidden={Boolean(projectId) && activeTab !== 1}>
  <div class="card-header">
    <h2 id="sources-heading">{@render icon('books')} Source Library</h2>
    <button type="button" class="add-button" onclick={openAddDialog}>+ Add</button>
  </div>

  {#if error}
    <div class="error-banner" role="alert">{error} {#if loadFailed}<button type="button" class="retry" onclick={load}>Retry</button>{/if}</div>
  {/if}

  {#if loading}
    <div class="loading-state" role="status">Loading sources…</div>
  {:else if loadFailed}
    <!-- The error banner above already explains the failure and offers a retry. -->
  {:else if sources.length === 0}
    <div class="source-empty">
      <span class="source-icon">{@render icon('books', 24)}</span>
      <h3>No sources yet</h3>
      <p>Add your research sources to keep references organised.</p>
      <button type="button" class="primary-button" onclick={openAddDialog}>+ Add Source</button>
    </div>
  {:else}
    <ul class="source-list" role="list">
      {#each sources as source (source.id)}
        <li class="source-row">
          <div class="source-meta">
            <span class="source-title">{source.title}</span>
            {#if source.authors.length}
              <span class="source-authors">{source.authors.join(', ')}{source.year ? ` (${source.year})` : ''}</span>
            {:else if source.year}
              <span class="source-authors">{source.year}</span>
            {/if}
            <span class="source-ref" title={source.file_ref}>{source.file_ref}</span>
          </div>
          <div class="source-actions">
            <button
              type="button"
              class="icon-button"
              onclick={() => openEditDialog(source)}
              aria-label="Edit {source.title}"
              title="Edit metadata"
            >{@render icon('edit')}</button>
            <button
              type="button"
              class="icon-button danger"
              onclick={() => handleRemove(source)}
              aria-label="Remove {source.title}"
              title="Remove source"
            >{@render icon('trash')}</button>
          </div>
        </li>
      {/each}
    </ul>
  {/if}

  </div>
  <div id="source-panel-0" role={projectId ? 'tabpanel' : undefined} aria-labelledby={projectId ? 'source-tab-0' : undefined} hidden={!projectId || activeTab !== 0}>
  {#if textError}
    <div class="error-banner" role="alert">{textError}</div>
  {/if}
  <!-- Text source endpoints are project-scoped; without a project there is nothing to show. -->
  {#key projectId}
    {#if !projectId}
      <!-- no project selected -->
    {:else if textView === 'form'}
      <TextSourceForm {projectId} source={textEditing} onsaved={handleTextSaved} oncancel={closeTextForm} />
    {:else}
      <TextSourceList {projectId} oncreate={openTextCreate} onedit={openTextEdit} refreshKey={textRefresh} />
    {/if}
    {#if projectId}
      <dialog class="text-dialog" bind:this={createTextDialog} aria-labelledby="new-text-title" onclose={() => { if (textView === 'create') closeTextForm(); }}>
        {#if textView === 'create'}
          <header><h2 id="new-text-title">Add Text Source</h2><button type="button" aria-label="Close" onclick={closeTextForm}>×</button></header>
          <TextSourceForm {projectId} modal onsaved={handleTextSaved} oncancel={closeTextForm} />
        {/if}
      </dialog>
    {/if}
  {/key}
  </div>
</aside>

<!-- Add dialog -->
<dialog bind:this={addDialog} class="input-dialog" aria-labelledby="add-dialog-title">
  <form onsubmit={handleAdd}>
    <h3 id="add-dialog-title">Add Source</h3>

    <label>
      Title <span class="required">*</span>
      <input bind:value={addTitle} maxlength="256" required placeholder="e.g., The Structure of Scientific Revolutions" />
    </label>

    <label>
      Authors <span class="hint">(comma-separated)</span>
      <input bind:value={addAuthorsRaw} placeholder="e.g., Thomas Kuhn, Paul Feyerabend" />
    </label>

    <label>
      Year
      <input bind:value={addYear} type="number" min="1" max="9999" placeholder="e.g., 1962" />
    </label>

    <label>
      File reference <span class="required">*</span>
      <input bind:value={addFileRef} required placeholder="e.g., kuhn1962.pdf" />
    </label>

    {#if addError}
      <p class="field-error" role="alert">{addError}</p>
    {/if}

    <div class="dialog-actions">
      <button type="button" onclick={() => addDialog?.close()}>Cancel</button>
      <button type="submit" class="primary" disabled={addBusy}>
        {addBusy ? 'Adding…' : 'Add Source'}
      </button>
    </div>
  </form>
</dialog>

<!-- Edit dialog -->
<dialog bind:this={editDialog} class="input-dialog" aria-labelledby="edit-dialog-title">
  <form onsubmit={handleEdit}>
    <h3 id="edit-dialog-title">Edit Source</h3>

    <label>
      Title <span class="required">*</span>
      <input bind:value={editTitle} maxlength="256" required placeholder="Title" />
    </label>

    <label>
      Authors <span class="hint">(comma-separated)</span>
      <input bind:value={editAuthorsRaw} placeholder="e.g., Thomas Kuhn" />
    </label>

    <label>
      Year
      <input bind:value={editYear} type="number" min="1" max="9999" placeholder="e.g., 1962" />
    </label>

    {#if editError}
      <p class="field-error" role="alert">{editError}</p>
    {/if}

    <div class="dialog-actions">
      <button type="button" onclick={() => editDialog?.close()}>Cancel</button>
      <button type="submit" class="primary" disabled={editBusy}>
        {editBusy ? 'Saving…' : 'Save'}
      </button>
    </div>
  </form>
</dialog>

<style>
  .text-dialog { width:min(650px,calc(100% - 32px)); max-height:90dvh; overflow:auto; box-sizing:border-box; padding:clamp(18px,3vw,28px); border:1px solid #c9d7cc; border-radius:16px; color:#20392b; background:#fafcf9; box-shadow:0 20px 64px #142c2240; }
  .text-dialog::backdrop { background:#182a2166; }
  .text-dialog header { display:flex; align-items:center; justify-content:space-between; margin-bottom:18px; }
  .text-dialog h2 { margin:0; font:700 22px var(--sans); }
  .text-dialog header button { width:36px; height:36px; border:0; background:transparent; color:inherit; font-size:24px; cursor:pointer; }

  .source-card, .source-card * { box-sizing: border-box; }
  button { font: inherit; color: inherit; cursor: pointer; }
  button:disabled { cursor: default; opacity: 1; }
  button:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }

  .surface { background: var(--surface); border: 1.5px solid transparent; border-radius: 14px; box-shadow: var(--shadow); }
  .source-tabs { display:flex; margin:0 0 16px; border-bottom:1px solid #dce6de; }
  .source-tabs button { flex:1; padding:9px 4px; border:0; border-bottom:2px solid transparent; background:transparent; color:#526359; font:600 12px var(--sans); }
  .source-tabs button[aria-selected=true] { color:#234836; border-bottom-color:#365d46; }
  .source-tabs button:hover { background:#eef5ef; }
  .source-card { padding: 20px; }

  .card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
  h2 { display: flex; align-items: center; gap: 7px; font-size: 10.5px; text-transform: uppercase; letter-spacing: .04em; font-weight: 700; margin: 0; }

  .add-button { display: inline-flex; align-items: center; justify-content: center; gap: 6px; font-size: 10px; font-weight: 600; border-radius: 7px; padding: 6px 11px; border: 1px solid var(--border); background: #f4f5f3; white-space: nowrap; }
  .add-button:hover { background: #eaece9; }

  .error-banner { background: #fdf0f0; border: 1px solid #e8b4b4; border-radius: 8px; color: #b94040; font-size: 10.5px; padding: 9px 12px; margin-bottom: 12px; display: flex; align-items: center; gap: 10px; }
  .error-banner .retry { font-size: 10px; font-weight: 600; color: #b94040; background: transparent; border: 1px solid currentColor; border-radius: 5px; padding: 3px 9px; }
  .loading-state { padding: 24px 12px; text-align: center; color: var(--text-muted); font-size: 10.5px; }

  .source-empty { border: 1px solid #e2e6e2; border-radius: 9px; background: var(--surface-muted); padding: 20px 12px; text-align: center; }
  .source-empty h3 { margin: 0 0 6px; font-size: 11px; }
  .source-empty p { margin: 0 0 12px; color: #78867f; font-size: 10px; line-height: 1.6; }
  .source-icon { display: inline-flex; color: var(--accent-border); margin-bottom: 8px; }
  .primary-button { display: inline-flex; align-items: center; justify-content: center; gap: 6px; font-size: 10.5px; font-weight: 600; border-radius: 7px; padding: 8px 14px; border: 1px solid var(--accent); background: var(--accent); color: white; white-space: nowrap; }
  .primary-button:hover { background: var(--accent-hover); }

  .source-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; }
  .source-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; padding: 10px 12px; border: 1px solid #e2e6e2; border-radius: 8px; background: var(--surface-muted, #f9faf9); }
  .source-meta { display: grid; gap: 2px; min-width: 0; }
  .source-title { font-size: 11px; font-weight: 600; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .source-authors { font-size: 10px; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .source-ref { font: 9.5px var(--mono, monospace); color: #8fa498; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

  .source-actions { display: flex; gap: 4px; flex-shrink: 0; }
  .icon-button { display: flex; align-items: center; justify-content: center; border: 1px solid transparent; border-radius: 5px; padding: 4px; background: transparent; color: var(--text-muted); }
  .icon-button:hover { background: #eaece9; border-color: var(--border); color: var(--text); }
  .icon-button.danger:hover { background: #fdf0f0; border-color: #e8b4b4; color: #b94040; }

  /* Dialogs */
  .input-dialog { width: min(380px, calc(100vw - 32px)); border: 1px solid var(--accent-border); border-radius: 12px; padding: 22px; background: var(--surface); color: var(--text); font: 12px var(--sans); box-shadow: 0 20px 60px #19282233; }
  .input-dialog::backdrop { background: #19282255; }
  .input-dialog h3 { font-size: 14px; margin: 0 0 16px; font-weight: 700; }
  .input-dialog label { display: grid; gap: 6px; margin-bottom: 12px; font-size: 11px; }
  .input-dialog input { width: 100%; padding: 9px; border: 1px solid #aeb9b3; border-radius: 6px; background: white; color: var(--text); font: inherit; }
  .required { color: #b94040; }
  .hint { font-size: 10px; color: var(--text-muted); font-weight: 400; }
  .field-error { color: #b94040; font-size: 10.5px; margin: 4px 0 0; }
  .dialog-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 18px; }
  .dialog-actions button { border: 1px solid #aeb9b3; border-radius: 6px; padding: 7px 14px; font-size: 11px; }
  .dialog-actions .primary { background: var(--accent); color: white; border-color: var(--accent); }
  .dialog-actions .primary:not(:disabled):hover { background: var(--accent-hover); }
  .dialog-actions .primary:disabled { opacity: 0.65; cursor: default; }

  @media(max-width: 767px) { .source-card { margin-top: 4px; } }
</style>
