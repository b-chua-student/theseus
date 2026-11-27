<script>
  import {
    listProjects,
    createProject,
    deleteProject,
    renameProject,
    editProjectDescription,
    removeProjectDescription,
    transferProjectOwnership,
  } from '../lib/api/projects.js';

  let { user, onworkspace, onproject } = $props();

  // ── project list ──────────────────────────────────────────────────────────
  let projects  = $state([]);
  let loading   = $state(true);
  let error     = $state('');
  let loadFailed = $state(false);

  $effect(() => { load(); });

  async function load() {
    loading = true;
    error   = '';
    loadFailed = false;
    try { projects = await listProjects(); }
    catch (e) { error = e.message; loadFailed = true; }
    finally { loading = false; }
  }

  // ── create modal ──────────────────────────────────────────────────────────
  let createModal;
  let newName        = $state('');
  let newDescription = $state('');
  let submitting     = $state(false);

  function openCreate() {
    newName        = '';
    newDescription = '';
    createModal.showModal();
  }

  async function submitCreate(event) {
    event.preventDefault();
    if (!newName.trim() || submitting) return;
    submitting = true;
    try {
      await createProject(newName.trim());
      // persist description if provided
      if (newDescription.trim()) {
        const fresh = await listProjects();
        const created = fresh.find(p => p.name === newName.trim());
        if (created) await editProjectDescription(created.id, newDescription.trim());
      }
      createModal.close();
      await load();
    } catch (e) {
      error = e.message;
    } finally {
      submitting = false;
    }
  }

  // ── rename modal ──────────────────────────────────────────────────────────
  let renameModal;
  let renameTarget = $state(null);   // { id, name }
  let renameName   = $state('');

  function openRename(project) {
    renameTarget = project;
    renameName   = project.name;
    renameModal.showModal();
  }

  async function submitRename(event) {
    event.preventDefault();
    if (!renameName.trim() || !renameTarget) return;
    try {
      await renameProject(renameTarget.id, renameName.trim());
      renameModal.close();
      await load();
    } catch (e) {
      error = e.message;
    }
  }

  // ── edit description modal ────────────────────────────────────────────────
  let descModal;
  let descTarget = $state(null);   // { id, description }
  let descText   = $state('');

  function openDesc(project) {
    descTarget = project;
    descText   = project.description ?? '';
    descModal.showModal();
  }

  async function submitDesc(event) {
    event.preventDefault();
    if (!descTarget) return;
    try {
      const trimmed = descText.trim();
      if (trimmed) {
        await editProjectDescription(descTarget.id, trimmed);
      } else {
        await removeProjectDescription(descTarget.id);
      }
      descModal.close();
      await load();
    } catch (e) {
      error = e.message;
    }
  }

  // ── delete ────────────────────────────────────────────────────────────────
  async function handleDelete(project) {
    if (!confirm(`Delete "${project.name}"? This cannot be undone.`)) return;
    try {
      await deleteProject(project.id);
      await load();
    } catch (e) {
      error = e.message;
    }
  }

  // ── transfer ownership modal ──────────────────────────────────────────────
  let ownerModal;
  let ownerTarget  = $state(null);   // full project object
  let ownerNewId   = $state('');

  function openTransfer(project) {
    ownerTarget = project;
    ownerNewId  = '';
    ownerModal.showModal();
  }

  async function submitTransfer(event) {
    event.preventDefault();
    if (!ownerNewId.trim() || !ownerTarget) return;
    try {
      await transferProjectOwnership(ownerTarget.id, ownerNewId.trim());
      ownerModal.close();
      await load();
    } catch (e) {
      error = e.message;
    }
  }
</script>

<!-- ── banner ───────────────────────────────────────────────────────────── -->
<div class="projects-page">
<section class="banner">
  <div>
    <span class="eyebrow">THESEUS PROJECTS</span>
    <h1>Welcome {user?.display_name || 'Researcher'}! Let's Continue Your Research Projects</h1>
    <p>Select a project to view its manuscripts and source library.</p>
  </div>
</section>

<!-- ── project grid ─────────────────────────────────────────────────────── -->
<main>
  <div class="toolbar">
    <span>YOUR PROJECTS · {projects.length}</span>
    <button onclick={onworkspace}>Open existing manuscript workspace ↗</button>
  </div>

  {#if error}
    <p class="error" role="alert">{error} <button type="button" class="retry" onclick={load}>Retry</button></p>
  {/if}

  {#if loading}
    <div class="grid" role="status" aria-label="Loading projects">
      {#each { length: 3 }, i (i)}<div class="card skeleton"></div>{/each}
    </div>
  {:else}
  <div class="grid">
    <button class="card new" onclick={openCreate}>
      <span class="plus">+</span>
      <strong>New Project</strong>
      <small>Create a research workspace</small>
    </button>

    {#if projects.length === 0 && !loadFailed}
      <div class="card empty-hint">
        <strong>No projects yet</strong>
        <small>Create your first project to start a manuscript.</small>
      </div>
    {:else}
      {#each projects as project (project.id)}
        <article class="card">
          <!-- action row — clicks here must NOT open the project -->
          <div class="card-actions">
            <button
              class="action-btn"
              title="Rename project"
              onclick={(e) => { e.stopPropagation(); openRename(project); }}
              aria-label="Rename {project.name}"
            >✎</button>
            <button
              class="action-btn"
              title="Edit description"
              onclick={(e) => { e.stopPropagation(); openDesc(project); }}
              aria-label="Edit description of {project.name}"
            >≡</button>
            {#if project.members.length > 0}
              <button
                class="action-btn"
                title="Transfer ownership"
                onclick={(e) => { e.stopPropagation(); openTransfer(project); }}
                aria-label="Transfer ownership of {project.name}"
              >⇄</button>
            {/if}
            <button
              class="action-btn danger"
              title="Delete project"
              onclick={(e) => { e.stopPropagation(); handleDelete(project); }}
              aria-label="Delete {project.name}"
            >✕</button>
          </div>

          <!-- clickable body navigates to the project -->
          <button class="card-body" onclick={() => onproject?.(project)}>
            <h2>{project.name}</h2>
            <p class="desc">{project.description || 'No description added.'}</p>
            <div class="meta">
              {project.members.length} member{project.members.length !== 1 ? 's' : ''}
              · created {new Date(project.created_at).toLocaleDateString()}
            </div>
          </button>
        </article>
      {/each}
    {/if}
  </div>
  {/if}
</main>
</div>

<!-- ── create project modal ─────────────────────────────────────────────── -->
<dialog bind:this={createModal} aria-labelledby="create-title">
  <header>
    <strong id="create-title">New Project</strong>
    <button onclick={() => createModal.close()} aria-label="Close">×</button>
  </header>

  <form onsubmit={submitCreate}>
    <label>
      Project Name
      <input bind:value={newName} required maxlength="50" placeholder="e.g., My Thesis…" />
    </label>

    <label>
      Description <span class="optional">(optional)</span>
      <input bind:value={newDescription} maxlength="500" placeholder="A short description…" />
    </label>

    <footer>
      <button class="green" type="submit" disabled={submitting}>
        {submitting ? 'Creating…' : 'Create +'}
      </button>
    </footer>
  </form>
</dialog>

<!-- ── rename modal ─────────────────────────────────────────────────────── -->
<dialog bind:this={renameModal} aria-labelledby="rename-title">
  <header>
    <strong id="rename-title">Rename Project</strong>
    <button onclick={() => renameModal.close()} aria-label="Close">×</button>
  </header>

  <form onsubmit={submitRename}>
    <label>
      New Name
      <input bind:value={renameName} required maxlength="50" placeholder="Project name…" />
    </label>

    <footer>
      <button class="green" type="submit">Save</button>
    </footer>
  </form>
</dialog>

<!-- ── edit description modal ───────────────────────────────────────────── -->
<dialog bind:this={descModal} aria-labelledby="desc-title">
  <header>
    <strong id="desc-title">Edit Description</strong>
    <button onclick={() => descModal.close()} aria-label="Close">×</button>
  </header>

  <form onsubmit={submitDesc}>
    <label>
      Description
      <textarea bind:value={descText} rows="4" placeholder="Leave blank to remove description…"></textarea>
    </label>
    <p class="hint">Leave blank to clear the description.</p>

    <footer>
      <button class="green" type="submit">Save</button>
    </footer>
  </form>
</dialog>

<!-- ── transfer ownership modal ─────────────────────────────────────────── -->
<dialog bind:this={ownerModal} aria-labelledby="owner-title">
  <header>
    <strong id="owner-title">Transfer Ownership</strong>
    <button onclick={() => ownerModal.close()} aria-label="Close">×</button>
  </header>

  <form onsubmit={submitTransfer}>
    <p class="hint">Choose a current member to become the new owner of <strong>{ownerTarget?.name}</strong>.</p>

    <label>
      New Owner
      <select bind:value={ownerNewId} required>
        <option value="" disabled>Select a member…</option>
        {#each ownerTarget?.members ?? [] as m (m.id)}
          <option value={m.id}>{m.display_name}</option>
        {/each}
      </select>
    </label>

    <footer>
      <button class="green" type="submit">Transfer</button>
    </footer>
  </form>
</dialog>

<style>
  /* ── banner ── */
  .projects-page {
    position: relative;
    isolation: isolate;
    overflow: hidden;
    min-height: calc(100svh - 48px);
    background: #eaf1eb;
  }
  .projects-page::before {
    content: '';
    position: absolute;
    inset: -15%;
    z-index: -1;
    pointer-events: none;
    background: radial-gradient(ellipse at 16% 42%, #add5c2, transparent 48%),
      radial-gradient(ellipse at 84% 65%, #ffffff, transparent 46%);
  }
  .banner {
    padding: clamp(36px, 6vw, 76px) 24px;
    background: linear-gradient(112deg, #304f42, #406755dd);
    color: white;
  }
  .banner > div, main { max-width: 960px; margin: auto; }
  .eyebrow { font: 11px var(--mono); letter-spacing: .1em; }
  h1 { font-size: clamp(26px, 3vw, 40px); max-width: 700px; line-height: 1.16; letter-spacing: -.03em; margin: 12px 0; overflow-wrap: anywhere; }
  p { font-size: 14px; line-height: 1.6; }
  main { padding: 40px 24px 64px; }

  .toolbar {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    align-items: center;
    margin-bottom: 20px;
    font: 10px var(--mono);
  }

  button { cursor: pointer; }

  .toolbar button {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 8px;
    font: 11px var(--sans);
  }

  /* ── grid ── */
  .grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 20px;
  }

  .card {
    background: var(--surface);
    padding: 0;
    border: 1px solid #cbdacf;
    border-radius: 14px;
    min-height: 200px;
    box-shadow: 0 8px 24px #203d2f10;
    overflow-wrap: anywhere;
    display: flex;
    flex-direction: column;
  }

  .new {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 24px;
  }
  .new { background: linear-gradient(145deg, #fff, #f0f7f1); }
  :is(.new, article.card):focus-within {
    border-color: #62866f;
    box-shadow: 0 8px 24px #203d2f24;
  }
  @media (hover: hover) {
    :is(.new, article.card):hover {
      border-color: #83a891;
      box-shadow: 0 12px 26px -6px #224a3538;
    }
    .new:hover .plus { background: #315943; color: white; }
  }
  .new:focus-visible .plus { background: #315943; color: white; }
  .plus { display: grid; place-items: center; width: 48px; height: 48px; border-radius: 14px; background: #e0eee4; color: #304f42; font-size: 30px; }

  /* ── card internals ── */
  .card-actions {
    display: flex;
    justify-content: flex-end;
    gap: 4px;
    padding: 10px 12px 0;
    flex-shrink: 0;
  }

  .action-btn {
    background: none;
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 12px;
    color: var(--text-muted);
    line-height: 1.4;
  }
  .action-btn:hover { background: var(--border); color: var(--text); }
  .action-btn.danger:hover { background: #fde8e8; color: #c0392b; border-color: #c0392b; }

  .card-body {
    flex: 1;
    display: flex;
    flex-direction: column;
    text-align: left;
    background: none;
    border: none;
    padding: 12px 24px 20px;
    border-radius: 0 0 14px 14px;
    width: 100%;
    font: inherit;
    color: inherit;
  }
  .card-body:hover { background: #eff6f080; }
  .card-body:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; border-radius: 0 0 14px 14px; }

  h2 { font-size: 18px; margin: 0 0 8px; }

  .desc { font-size: 13px; line-height: 1.6; margin: 0; color: var(--text-muted); flex: 1; }

  .meta {
    margin-top: 16px;
    font-size: 10px;
    color: var(--text-muted);
  }

  /* ── status ── */
  .error { font-size: 11px; color: #c0392b; margin-bottom: 12px; display: flex; align-items: center; gap: 10px; }
  .error .retry { font-size: 10px; font-weight: 600; color: var(--accent); background: transparent; border: 1px solid currentColor; border-radius: 5px; padding: 3px 9px; }
  .skeleton { background: linear-gradient(90deg, #eef1ee 25%, #f6f8f6 37%, #eef1ee 63%); background-size: 400% 100%; animation: shimmer 1.4s ease infinite; border: 1px solid var(--border, #e2e6e2); }
  @keyframes shimmer { 0% { background-position: 100% 0; } 100% { background-position: 0 0; } }
  .empty-hint { display: flex; flex-direction: column; justify-content: center; align-items: flex-start; gap: 4px; color: var(--text-muted); padding: 20px; }
  .empty-hint small { font-size: 10px; }

  /* ── dialogs ── */
  dialog {
    padding: 0;
    width: calc(100% - 32px);
    max-width: 365px;
    max-height: 90dvh;
    overflow: auto;
    border: 1.5px solid #526b60;
    border-radius: 12px;
    background: var(--surface);
    color: var(--text);
    box-shadow: 0 18px 45px #19282238;
  }
  dialog::backdrop { background: #17251e66; backdrop-filter: blur(3px); }

  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 20px;
    border-bottom: 1px solid var(--border);
    font-size: 11px;
  }
  header button { border: 0; background: none; font-size: 18px; }

  form { padding: 20px; display: grid; gap: 16px; }

  label { display: grid; gap: 8px; font-size: 13px; font-weight: 700; }

  .optional { font-weight: 400; color: var(--text-muted); }

  input, textarea, select {
    width: 100%;
    min-width: 0;
    padding: 7px 12px;
    background: white;
    border: 1px solid var(--border);
    border-radius: 6px;
    font-size: 11px;
    font-family: inherit;
    box-sizing: border-box;
  }
  textarea { resize: vertical; }

  .hint { font-size: 10px; color: var(--text-muted); margin: 0; }

  footer { text-align: right; }

  .green {
    background: var(--accent);
    color: white;
    border: 0;
    border-radius: 5px;
    padding: 7px 16px;
    font-size: 10.5px;
  }
  .green:disabled { opacity: 0.6; cursor: not-allowed; }

  .toolbar button:hover, header button:hover { background-color: #e3eee6; }

  dialog header { background: #edf4ee; font-size: 15px; }
  .green:hover:not(:disabled) { background-color: #29483b; }
  @media (prefers-reduced-motion: no-preference) {
    :is(.new, article.card) { transition: transform 200ms ease, box-shadow 200ms ease, border-color 200ms ease; }
    .plus { transition: background-color 180ms ease, color 180ms ease; }
    @media (hover: hover) {
      :is(.new, article.card):hover { transform: translateY(-3px); }
    }
    .projects-page::before { animation: project-wave 12s ease-in-out infinite alternate; }
    button { transition: background-color 180ms ease, color 180ms ease, border-color 180ms ease, transform 140ms ease; }
    button:active:not(:disabled) { transform: scale(.985); }
  }
  @keyframes project-wave {
    from { transform: translate(-5%, -2%) rotate(-3deg); }
    to { transform: translate(5%, 2%) rotate(3deg); }
  }
  @media (prefers-reduced-motion: reduce) {
    .skeleton { animation: none; }
  }

  /* ── responsive ── */
  @media (max-width: 760px) {
    .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  }
  @media (max-width: 500px) {
    .grid { grid-template-columns: 1fr; }
    main { padding: 28px 16px; }
    .toolbar { flex-direction: column; align-items: flex-start; }
  }
</style>
