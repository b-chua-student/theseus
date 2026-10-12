<script>
  import { onMount } from "svelte";
  import { Editor } from "@tiptap/core";
  import StarterKit from "@tiptap/starter-kit";

  let { id, onback } = $props();

  let element;
  let editor = $state.raw(null);
  let tick = $state(0);

  const active = (name, attrs) => (tick, editor?.isActive(name, attrs));

  const tools = [
    { label: "Bold", name: "bold", run: (c) => c.toggleBold() },
    { label: "Italic", name: "italic", run: (c) => c.toggleItalic() },
    { label: "H1", name: "heading", attrs: { level: 1 }, run: (c) => c.toggleHeading({ level: 1 }) },
    { label: "H2", name: "heading", attrs: { level: 2 }, run: (c) => c.toggleHeading({ level: 2 }) },
    { label: "Bullets", name: "bulletList", run: (c) => c.toggleBulletList() },
    { label: "Numbered", name: "orderedList", run: (c) => c.toggleOrderedList() },
    { label: "Code", name: "codeBlock", run: (c) => c.toggleCodeBlock() },
    { label: "Undo", run: (c) => c.undo() },
    { label: "Redo", run: (c) => c.redo() },
  ];

  onMount(() => {
    editor = new Editor({
      element,
      extensions: [StarterKit],
      content: "",
      onTransaction: () => tick++,
    });

    fetch(`/api/documents/${id}`)
      .then((r) => r.json())
      .then((doc) => editor.commands.setContent(doc.content));

    return () => editor.destroy();
  });

  async function save() {
    await fetch("/api/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ document_id: id, content: editor.getHTML() }),
    });
  }
</script>

<div class="bar">
  <button onclick={onback}>← Back</button>
  <h2 class="name">{id}</h2>
  {#each tools as t}
    <button
      class:active={t.name && active(t.name, t.attrs)}
      onclick={() => t.run(editor.chain().focus()).run()}
    >
      {t.label}
    </button>
  {/each}
  <button onclick={save}>Save</button>
</div>

<div bind:this={element}></div>

<style>
  .bar { display: flex; gap: 0.25rem; flex-wrap: wrap; align-items: center; margin-bottom: 1rem; }
  .name { width: 100%; margin: 0.5rem 0; font-size: 1.25rem; }
  .active { background: #ece9fd; }
  :global(.tiptap) { outline: none; min-height: 300px; padding: 0.5rem; border: 1px solid #ddd; }
  :global(.tiptap pre) { background: #2e2b29; color: #fff; padding: 0.75rem 1rem; border-radius: 0.5rem; }
</style>
