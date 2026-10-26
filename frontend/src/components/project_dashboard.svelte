<script lang="ts">
  import { onMount } from 'svelte';

  type Project = { id: string; owner_id: string; name: string };
  type Manuscript = { id: string; project_id: string; title: string };

  // Matches FakeProjectRepository.OWNER_ID — the seeded owner used for new projects.
  const OWNER_ID = '00000000-0000-0000-0000-0000000000a1';

  let { onopen }: { onopen?: (m: { id: string; projectId: string; ownerId: string; title: string }) => void } = $props();

  type User = { id: string; email: string; display_name: string };

  let projects = $state<Project[]>([]);
  let manuscripts = $state<Record<string, Manuscript[]>>({});
  let currentUser = $state<User | null>(null);
  let loading = $state(true);
  let error = $state<string | null>(null);

  let newName = $state('');
  let editingId = $state<string | null>(null);
  let editingName = $state('');

  // Per-project: controls the "new manuscript" form
  let creatingFor = $state<string | null>(null);
  let newManuscriptTitle = $state('');

  const totalManuscripts = $derived(
    Object.values(manuscripts).reduce((sum, list) => sum + list.length, 0)
  );

  async function api<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await fetch(`/api${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...init
    });
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      const detail = body?.error;
      throw new Error(typeof detail === 'string' ? detail : `Request failed (${res.status})`);
    }
    return res.status === 204 ? (undefined as T) : res.json();
  }

  async function loadManuscripts(project: Project) {
    manuscripts[project.id] = await api<Manuscript[]>(
      `/users/${project.owner_id}/projects/${project.id}/manuscripts`
    );
  }

  async function load() {
    loading = true;
    error = null;
    try {
      [projects, currentUser] = await Promise.all([
        api<Project[]>('/projects'),
        api<User>(`/users/${OWNER_ID}`)
      ]);
      await Promise.all(projects.map(loadManuscripts));
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load projects';
    } finally {
      loading = false;
    }
  }

  async function createProject(event: SubmitEvent) {
    event.preventDefault();
    const name = newName.trim();
    if (!name) return;
    try {
      const project = await api<Project>('/projects', {
        method: 'POST',
        body: JSON.stringify({ owner_id: OWNER_ID, name })
      });
      projects.push(project);
      manuscripts[project.id] = [];
      newName = '';
    } catch (e) {
      error = e instanceof Error ? e.message : 'Create failed';
    }
  }

  async function createManuscript(project: Project, event: SubmitEvent) {
    event.preventDefault();
    const title = newManuscriptTitle.trim();
    if (!title) return;
    try {
      const manuscript = await api<Manuscript>(
        `/users/${project.owner_id}/projects/${project.id}/manuscripts`,
        { method: 'POST', body: JSON.stringify({ title }) }
      );
      manuscripts[project.id] = [...(manuscripts[project.id] ?? []), manuscript];
      newManuscriptTitle = '';
      creatingFor = null;
    } catch (e) {
      error = e instanceof Error ? e.message : 'Create manuscript failed';
    }
  }

  function startEdit(project: Project) {
    editingId = project.id;
    editingName = project.name;
  }

  async function saveEdit(project: Project) {
    const name = editingName.trim();
    if (!name || name === project.name) {
      editingId = null;
      return;
    }
    try {
      const updated = await api<Project>(`/projects/${project.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ name })
      });
      projects = projects.map((p) => (p.id === updated.id ? updated : p));
      editingId = null;
    } catch (e) {
      error = e instanceof Error ? e.message : 'Update failed';
    }
  }

  async function deleteProject(project: Project) {
    if (!confirm(`Delete "${project.name}"?`)) return;
    try {
      await api<void>(`/projects/${project.id}`, { method: 'DELETE' });
      projects = projects.filter((p) => p.id !== project.id);
      delete manuscripts[project.id];
    } catch (e) {
      error = e instanceof Error ? e.message : 'Delete failed';
    }
  }

  function openManuscript(project: Project, m: Manuscript) {
    onopen?.({ id: m.id, projectId: project.id, ownerId: project.owner_id, title: m.title });
  }

  onMount(load);
</script>

<main>
  <header>
    <h1>Projects</h1>
    <div class="header-right">
      {#if currentUser}
        <span class="display-name">{currentUser.display_name}</span>
      {/if}
      <p class="stats">{projects.length} projects · {totalManuscripts} manuscripts</p>
    </div>
  </header>

  <form class="create" onsubmit={createProject}>
    <input bind:value={newName} placeholder="New project name" required />
    <button type="submit">Create</button>
  </form>

  {#if error}
    <p class="error" role="alert">
      {error}
      <button class="link" onclick={() => (error = null)}>Dismiss</button>
    </p>
  {/if}

  {#if loading}
    <p>Loading…</p>
  {:else if projects.length === 0}
    <p class="empty">No projects yet.</p>
  {:else}
    <ul class="grid">
      {#each projects as project (project.id)}
        <li class="card">
          {#if editingId === project.id}
            <form
              onsubmit={(e) => {
                e.preventDefault();
                saveEdit(project);
              }}
            >
              <!-- svelte-ignore a11y_autofocus -->
              <input bind:value={editingName} autofocus />
              <div class="actions">
                <button type="submit">Save</button>
                <button type="button" class="link" onclick={() => (editingId = null)}>
                  Cancel
                </button>
              </div>
            </form>
          {:else}
            <h2>{project.name}</h2>
            <p class="count">{manuscripts[project.id]?.length ?? 0} manuscripts</p>
            <ul class="manuscript-list">
              {#each (manuscripts[project.id] ?? []) as m (m.id)}
                <li class="manuscript-item">
                  <span class="manuscript-title">{m.title}</span>
                  <button class="link open-btn" onclick={() => openManuscript(project, m)}>
                    Open →
                  </button>
                </li>
              {/each}
            </ul>

            {#if creatingFor === project.id}
              <form
                class="new-manuscript"
                onsubmit={(e) => createManuscript(project, e)}
              >
                <!-- svelte-ignore a11y_autofocus -->
                <input
                  bind:value={newManuscriptTitle}
                  placeholder="Manuscript title"
                  autofocus
                  required
                />
                <div class="actions">
                  <button type="submit">Add</button>
                  <button
                    type="button"
                    class="link"
                    onclick={() => { creatingFor = null; newManuscriptTitle = ''; }}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            {:else}
              <div class="actions">
                <button class="link" onclick={() => (creatingFor = project.id)}>+ Manuscript</button>
                <button class="link" onclick={() => startEdit(project)}>Rename</button>
                <button class="link danger" onclick={() => deleteProject(project)}>Delete</button>
              </div>
            {/if}
          {/if}
        </li>
      {/each}
    </ul>
  {/if}
</main>

<style>
  main { max-width: 960px; margin: 0 auto; padding: 2rem 1rem; font-family: system-ui, sans-serif; }
  header { display: flex; justify-content: space-between; align-items: baseline; }
  .header-right { display: flex; flex-direction: column; align-items: flex-end; gap: 0.15rem; }
  .display-name { font-weight: 600; font-size: 0.95rem; color: #333; }
  .stats { color: #666; margin: 0; }
  .create { display: flex; gap: 0.5rem; margin: 1.5rem 0; }
  .create input { flex: 1; }
  input { padding: 0.5rem; border: 1px solid #ccc; border-radius: 6px; font: inherit; width: 100%; box-sizing: border-box; }
  button { padding: 0.5rem 1rem; border: 0; border-radius: 6px; background: #2b5fd9; color: #fff; cursor: pointer; font: inherit; }
  button.link { background: none; color: #2b5fd9; padding: 0.25rem 0.5rem; }
  button.danger { color: #c0392b; }
  .grid { list-style: none; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; }
  .card { border: 1px solid #e0e0e0; border-radius: 10px; padding: 1rem; }
  .card h2 { margin: 0 0 0.25rem; font-size: 1.1rem; }
  .count { color: #666; margin: 0 0 0.5rem; font-size: 0.9rem; }
  .manuscript-list { list-style: none; padding: 0; margin: 0 0 0.75rem; }
  .manuscript-item { display: flex; align-items: center; justify-content: space-between; padding: 0.2rem 0; font-size: 0.9rem; gap: 0.5rem; }
  .manuscript-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .open-btn { font-size: 0.8rem; flex-shrink: 0; }
  .new-manuscript { margin-top: 0.5rem; }
  .actions { display: flex; gap: 0.25rem; margin-top: 0.5rem; flex-wrap: wrap; }
  .error { background: #fdecea; color: #922; padding: 0.5rem 1rem; border-radius: 6px; }
  .empty { color: #666; }
</style>
