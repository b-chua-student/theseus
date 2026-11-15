<script>
  import Dashboard from './components/dashboard.svelte';
  import DocumentEditor from './components/editor.svelte';

  let documents = $state([]);
  let selectedId = $state(null);

  $effect(() => {
    load();
  });

  function load() {
    fetch('/api/documents')
      .then((r) => r.json())
      .then((data) => (documents = data));
  }

  async function create() {
    const name = prompt('Document name');
    if (!name) return;
    await fetch('/api/documents', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_id: name }),
    });
    selectedId = name;
  }

  function back() {
    selectedId = null;
    load();
  }
</script>

{#if selectedId === null}
  <Dashboard {documents} onselect={(id) => (selectedId = id)} oncreate={create} />
{:else}
  <DocumentEditor id={selectedId} onback={back} />
{/if}
