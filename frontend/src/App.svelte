<script>
  import AppHeader from "./components/shared/AppHeader.svelte";
  import { listManuscripts, createManuscript } from "./lib/api/manuscripts.js";
  import Dashboard from './pages/dashboard.svelte';
  import DocumentEditor from './pages/editor.svelte';

  let documents = $state([]);
  let selectedId = $state(null);

  $effect(() => {
    load();
  });

  function load() {
    listManuscripts()
      .then((r) => r.json())
      .then((data) => (documents = data));
  }

  async function create() {
    const name = prompt('Document name');
    if (!name) return;
    await createManuscript(name);
    selectedId = name;
  }

  function back() {
    selectedId = null;
    load();
  }
</script>

<AppHeader inEditor={selectedId !== null} documentTitle={selectedId ?? ''} manuscriptCount={documents.length} onworkspace={back} />

{#if selectedId === null}
  <Dashboard {documents} onselect={(id) => (selectedId = id)} oncreate={create} />
{:else}
  <div class="editor-screen">
    <DocumentEditor id={selectedId} onback={back} />
  </div>
{/if}


<style>
  /* Keep the document workspace below the shared 48px navigation. */
  .editor-screen {
    position: fixed;
    inset: 48px 0 0;
    z-index: 10;
    overflow: auto;
    background: #e3eae5;
    text-align: left;
    color-scheme: light;
  }

  /* Fill the viewport space below AppHeader. */
  .editor-screen > :global(.theseus-editor) {
    width: 100%;
    max-width: none;
    height: calc(100dvh - 48px);
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
      min-height: calc(100dvh - 48px);
    }
  }
</style>
