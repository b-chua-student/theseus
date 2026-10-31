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
  <div class="editor-screen">
    <DocumentEditor id={selectedId} onback={back} />
  </div>
{/if}


<style>
  /* Escape the centered app container only while a document is open. */
  .editor-screen {
    position: fixed;
    inset: 0;
    z-index: 10;
    overflow: auto;
    background: #e3eae5;
    text-align: left;
    color-scheme: light;
  }

  /* This app has no header above the editor. Use the full viewport height. */
  .editor-screen > :global(.theseus-editor) {
    width: 100%;
    max-width: none;
    height: 100dvh;
    min-height: 0;
    margin: 0;
  }

  /* Prevent the underlying dashboard container from scrolling behind the editor. */
  :global(body:has(.editor-screen)) {
    overflow: hidden;
  }

  /* Preserve the editor's stacked, scrollable layout on smaller screens. */
  @media (max-width: 1023px) {
    .editor-screen > :global(.theseus-editor) {
      height: auto;
      min-height: 100dvh;
    }
  }
</style>
