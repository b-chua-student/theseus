<script>
  import Dashboard from './components/dashboard.svelte';
  import ManuscriptEditor from './components/editor.svelte';

  let manuscripts = $state([]);
  let selectedId = $state(null);

  $effect(() => {
    load();
  });

  function load() {
    fetch('/api/manuscripts')
      .then((r) => r.json())
      .then((data) => (manuscripts = data));
  }

  async function create() {
    const title = prompt('Manuscript title');
    if (!title) return;
    const res = await fetch('/api/manuscripts/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    });
    if (!res.ok) return;
    const created = await res.json();
    selectedId = created.id;
  }

  async function remove(id) {
    const res = await fetch(`/api/manuscripts/${id}`, { method: 'DELETE' });
    if (res.ok) manuscripts = manuscripts.filter((m) => m.id !== id);
  }

  function back() {
    selectedId = null;
    load();
  }
</script>

{#if selectedId === null}
  <Dashboard
    {manuscripts}
    onselect={(id) => (selectedId = id)}
    oncreate={create}
    ondelete={remove}
  />
{:else}
  <ManuscriptEditor id={selectedId} onback={back} />
{/if}
