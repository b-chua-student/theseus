<script>
  let { documents = [], onselect, oncreate } = $props();
  let collabOpen = $state(false);

  const formatDate = (ts) => {
    if (ts === null || ts === undefined || ts === '') return 'Not available';
    const date = new Date(Number(ts) * 1000);
    return Number.isNaN(date.getTime()) ? 'Not available' : date.toLocaleString();
  };
  const commitLabel = (value) => typeof value === 'string' && value.length ? value.slice(0, 7) : 'No commit';
  function closePopover(event) {
    if (!event.target.closest?.('.collab-control')) collabOpen = false;
  }
</script>

<svelte:window onclick={closePopover} onkeydown={event => { if (event.key === 'Escape') collabOpen = false; }} />

{#snippet icon(name, size = 14)}
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    {#if name === 'document'}<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6M8 13h8M8 17h8"/>
    {:else if name === 'folder'}<path d="M3 7V5a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/>
    {:else if name === 'person'}<circle cx="12" cy="7" r="4"/><path d="M4 21v-2a4 4 0 0 1 4-4h8a4 4 0 0 1 4 4v2"/>
    {:else if name === 'clock'}<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
    {:else if name === 'books'}<path d="M4 4v16M8 4v16M12 4v16M16 5l4 14"/>
    {:else if name === 'back'}<path d="M19 12H5m7-7-7 7 7 7"/>
    {:else if name === 'close'}<path d="m6 6 12 12M18 6 6 18"/>
    {/if}
  </svg>
{/snippet}

<div class="theseus-dashboard">
  <header class="topbar">
    <div class="brand"><span class="brand-mark"></span><span>THESEUS</span></div>
    <span class="nav-divider"></span>
    <div class="breadcrumb"><span class="current">{@render icon('folder', 12)} Workspace</span><span class="chevron">›</span><span>Manuscripts</span><span class="count">{documents.length}</span></div>
  </header>

  <main class="dashboard-content">
    <div class="workspace-breadcrumb"><button type="button" disabled title="Project navigation is not connected">{@render icon('back')} All Theseus Projects</button><span>/</span><span class="workspace-badge">YOUR WORKSPACE</span></div>

    <section class="project-card surface" aria-labelledby="workspace-title">
      <div class="project-copy"><h1 id="workspace-title">Research Workspace</h1><p>Organize your manuscripts, review recent updates, and continue writing. Select a manuscript below or create a new document.</p></div>
      <div class="project-actions">
        <button type="button" class="new-button" onclick={() => oncreate?.()}><span class="plus">+</span> New Manuscript</button>
        <div class="collab-control">
          <button type="button" class="primary-button" onclick={() => collabOpen = !collabOpen} aria-expanded={collabOpen} aria-controls="collab-panel">{@render icon('person')} Collab <span class="plus">+</span></button>
          {#if collabOpen}
            <div class="collab-panel" id="collab-panel">
              <div class="popover-heading"><strong>Add Members</strong><button type="button" class="icon-button" onclick={() => collabOpen = false} aria-label="Close collaboration panel">{@render icon('close')}</button></div>
              <p>Collaboration is not available yet.</p>
              <label>SEARCH MEMBER<input disabled placeholder="Search Account" /></label>
              <button type="button" class="primary-button" disabled>Add +</button>
            </div>
          {/if}
        </div>
      </div>
    </section>

    <div class="dashboard-grid">
      <section aria-labelledby="manuscripts-heading">
        <div class="section-heading"><h2 id="manuscripts-heading">{@render icon('document')} Manuscripts ({documents.length})</h2><span>Click to open in editor</span></div>
        <div class="manuscript-list">
          {#each documents as doc (doc.document_id)}
            <button type="button" class="manuscript-card surface" onclick={() => onselect?.(doc.document_id)} aria-label={`Open manuscript ${doc.document_id}`}>
              <span class="card-top"><span class="document-badge">{@render icon('document', 11)} Manuscript</span><span class="modified">{@render icon('clock', 12)} {formatDate(doc.last_modified)}</span></span>
              <span class="document-title">{doc.document_id}</span>
              <span class="author">Author: {doc.author || 'Not specified'}</span>
              <span class="card-footer"><span class="commit">Last commit <code>{commitLabel(doc.last_commit_id)}</code></span><span class="open-label">Open Manuscript Editor <span>›</span></span></span>
            </button>
          {:else}
            <div class="empty-card surface"><span class="empty-icon">{@render icon('document', 25)}</span><h3>No manuscripts yet</h3><p>Create your first manuscript to start writing.</p><button type="button" class="primary-button" onclick={() => oncreate?.()}>+ New Manuscript</button></div>
          {/each}
        </div>
      </section>

      <aside class="source-card surface" aria-labelledby="sources-heading">
        <h2 id="sources-heading">{@render icon('books')} Project Source Library</h2>
        <div class="source-empty"><span class="source-icon">{@render icon('books', 24)}</span><h3>Your research sources</h3><p>Source uploads and reference management are not available yet.</p></div>
        <button type="button" class="source-upload" disabled title="Source upload is not connected">+ Upload Source</button>
      </aside>
    </div>
  </main>
</div>

<style>
  /* Shared fonts and theme come from index.html and app.css. */
  .theseus-dashboard { width: 100%; min-height: 100vh; min-height: 100dvh; flex: 1; color-scheme: light; background: var(--page-background); color: var(--text); font: 11px/1.5 var(--sans); text-align: left; }
  .theseus-dashboard * { box-sizing: border-box; }
  button,input { font: inherit; color: inherit; } button { cursor: pointer; } button:disabled { cursor: default; opacity: 1; } button:focus-visible,input:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }
  .topbar { height: 48px; display: flex; align-items: center; gap: 10px; padding: 0 24px; background: #fbfbf9; border-bottom: 1px solid #e2e6e2; position: sticky; top: 0; z-index: 20; }
  .brand { display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 11px; letter-spacing: .06em; }.brand-mark { width: 24px; height: 24px; border-radius: 6px; background: var(--accent); }.nav-divider { width: 1px; height: 16px; background: #e5e8e5; margin: 0 2px; }
  .breadcrumb { display: flex; align-items: center; gap: 8px; border: 1px solid #e0e4e0; border-radius: 7px; background: #f6f7f5; padding: 2px 8px 2px 2px; }.current { display: flex; align-items: center; gap: 6px; background: var(--accent); color: white; border-radius: 5px; padding: 4px 10px; font-weight: 500; }.chevron { color: #9aa59f; }.count { background: #e5ebe5; border-radius: 3px; font-size: 9px; padding: 0 5px; }
  .dashboard-content { max-width: 884px; margin: 0 auto; padding: 36px 32px 60px; }.workspace-breadcrumb { display: flex; align-items: center; gap: 8px; font-size: 10.5px; color: #5a6760; margin-bottom: 14px; }.workspace-breadcrumb button { display: inline-flex; align-items: center; gap: 6px; border: 0; background: none; padding: 0; font-weight: 500; }.workspace-badge { font: 600 9.5px var(--mono); padding: 4px 8px; border-radius: 4px; background: #dee5df; color: #2f3b35; }
  .surface { background: var(--surface); border: 1.5px solid transparent; border-radius: 14px; box-shadow: var(--shadow); }.project-card { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 28px; margin-bottom: 28px; }.project-copy { max-width: 450px; min-width: 0; }h1 { font-size: 20px; font-weight: 700; letter-spacing: -.025em; color: var(--text-h); margin: 0 0 8px; }.project-copy p { font-size: 10.5px; line-height: 1.6; color: var(--text-muted); margin: 0; }
  .project-actions { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }.new-button,.primary-button,.source-upload { display: inline-flex; align-items: center; justify-content: center; gap: 6px; font-size: 10.5px; font-weight: 600; border-radius: 7px; padding: 8px 14px; border: 1px solid var(--border); background: #f4f5f3; white-space: nowrap; }.new-button:hover { background: #eaece9; }.primary-button { background: var(--accent); color: white; border-color: var(--accent); }.primary-button:not(:disabled):hover { background: var(--accent-hover); }.plus { font-size: 14px; font-weight: 400; line-height: 1; }
  .dashboard-grid { display: grid; grid-template-columns: minmax(0,2fr) minmax(0,1fr); gap: 24px; align-items: start; }.section-heading { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin: 0 2px 12px; }h2 { display: flex; align-items: center; gap: 7px; font-size: 10.5px; text-transform: uppercase; letter-spacing: .04em; font-weight: 700; margin: 0; }.section-heading > span { font-size: 10px; color: var(--text-muted); }.manuscript-list { display: grid; gap: 16px; }
  .manuscript-card { display: block; width: 100%; padding: 20px; text-align: left; transition: transform .18s ease,border-color .18s ease,box-shadow .18s ease; }.manuscript-card:hover { transform: translateY(-2px); border-color: var(--accent); box-shadow: 0 10px 22px -4px rgb(30 45 38 / 16%); }.card-top { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; }.document-badge { display: inline-flex; align-items: center; gap: 5px; background: var(--accent); color: white; border-radius: 4px; padding: 3px 8px; font: 500 9px var(--mono); }.modified { display: inline-flex; align-items: center; gap: 4px; color: var(--text-muted); font-size: 9.5px; }.document-title { display: block; font-size: 14.5px; font-weight: 700; color: var(--text-h); margin-bottom: 4px; overflow-wrap: anywhere; }.author { display: block; font: 9.5px/1.5 var(--mono); color: var(--text-muted); margin-bottom: 14px; overflow-wrap: anywhere; }.card-footer { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; padding-top: 10px; border-top: 1px solid #e6eae6; }.commit { font: 9.5px var(--mono); color: #5a6760; }.commit code { font: inherit; color: var(--accent); margin-left: 6px; }.open-label { display: inline-flex; align-items: center; gap: 5px; font-size: 10px; font-weight: 700; }.open-label > span { font-size: 15px; }
  .source-card { padding: 20px; }.source-card h2 { margin-bottom: 14px; }.source-empty { border: 1px solid #e2e6e2; border-radius: 9px; background: var(--surface-muted); padding: 20px 12px; text-align: center; }.source-icon,.empty-icon { display: inline-flex; color: var(--accent-border); margin-bottom: 8px; }h3 { margin: 0 0 6px; font-size: 11px; }.source-empty p { margin: 0; color: #78867f; font-size: 10px; line-height: 1.6; }.source-upload { margin-top: 12px; width: 100%; color: #78867f; }.empty-card { padding: 36px 20px; text-align: center; }.empty-card h3 { font-size: 14px; }.empty-card p { color: var(--text-muted); margin: 0 0 16px; }
  .collab-control { position: relative; }.collab-panel { position: absolute; right: 0; top: calc(100% + 10px); z-index: 30; width: 235px; padding: 14px; border: 1.5px solid var(--accent-border); border-radius: 11px; background: var(--surface); box-shadow: 0 14px 34px #19282238; }.popover-heading { display: flex; justify-content: space-between; align-items: center; padding-bottom: 10px; border-bottom: 1px solid #e6eae6; }.icon-button { display: flex; border: 0; background: transparent; padding: 2px; }.collab-panel p { font-size: 10px; color: var(--text-muted); }.collab-panel label { display: grid; gap: 6px; font: 8px var(--mono); color: var(--text-muted); margin-bottom: 10px; }.collab-panel input { width: 100%; border: 1px solid var(--border); border-radius: 5px; padding: 8px; background: #f2f4f1; }.collab-panel .primary-button:disabled { background: #7c8d84; border-color: #7c8d84; }
  @media(max-width:767px) { .project-card { flex-direction: column; align-items: flex-start; padding: 24px; }.dashboard-grid { grid-template-columns: 1fr; }.dashboard-content { padding: 28px 16px 40px; }.source-card { margin-top: 4px; } }
  @media(max-width:420px) { .topbar { padding: 0 12px; gap: 7px; }.breadcrumb { gap: 5px; font-size: 10px; }.current { padding: 4px 6px; }.brand { font-size: 10px; gap: 6px; }.brand-mark { width: 21px; height: 21px; }.workspace-breadcrumb { flex-wrap: wrap; }.project-card { padding: 20px; }.section-heading { flex-wrap: wrap; }.manuscript-card { padding: 16px; }.project-actions { gap: 8px; }.new-button,.primary-button { padding: 8px 11px; } }
  @media(prefers-reduced-motion:reduce) { .manuscript-card { transition: none; }.manuscript-card:hover { transform: none; } }
</style>
