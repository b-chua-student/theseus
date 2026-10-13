<script>
  import { onMount } from "svelte";
  import { Editor } from "@tiptap/core";
  import StarterKit from "@tiptap/starter-kit";

  let { id, onback } = $props();

  let element;
  let editor = $state.raw(null);
  let tick = $state(0);

  let open = $state(false);
  let messages = $state([]);
  let input = $state("");
  let loading = $state(false);
  let log;

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

  function scrollDown() {
    queueMicrotask(() => log && (log.scrollTop = log.scrollHeight));
  }

  async function send() {
    const text = input.trim();
    if (!text || loading) return;
    messages.push({ role: "user", text });
    input = "";
    loading = true;
    scrollDown();
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          document_id: id,
          message: text,
          document: editor.getText(),
        }),
      });
      const data = await res.json();
      messages.push({ role: "assistant", text: data.reply });
    } catch {
      messages.push({ role: "assistant", text: "Request failed." });
    }
    loading = false;
    scrollDown();
  }

  function onkey(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }
</script>

<div class="layout">
  <div class="main">
    <div class="bar">
      <button onclick={onback}>← Back</button>
      <h2 class="name">{id}</h2>
      {#each tools as t (t.label)}
        <button
          class:active={t.name && active(t.name, t.attrs)}
          onclick={() => t.run(editor.chain().focus()).run()}
        >
          {t.label}
        </button>
      {/each}
      <button onclick={save}>Save</button>
      <button class:active={open} onclick={() => (open = !open)}>Chat</button>
    </div>

    <div bind:this={element}></div>
  </div>

  {#if open}
    <aside class="chat">
      <div class="chat-head">
        <span>Assistant</span>
        <button onclick={() => (open = false)}>✕</button>
      </div>
      <div class="log" bind:this={log}>
        {#each messages as m (m.id)}
          <div class="msg {m.role}">{m.text}</div>
        {/each}
        {#if loading}<div class="msg assistant">…</div>{/if}
      </div>
      <div class="chat-input">
        <textarea
          rows="2"
          placeholder="Ask something…"
          bind:value={input}
          onkeydown={onkey}
        ></textarea>
        <button onclick={send} disabled={loading}>Send</button>
      </div>
    </aside>
  {/if}
</div>

<style>
  .layout { display: flex; gap: 1rem; align-items: flex-start; }
  .main { flex: 1; min-width: 0; }
  .bar { display: flex; gap: 0.25rem; flex-wrap: wrap; align-items: center; margin-bottom: 1rem; }
  .name { width: 100%; margin: 0.5rem 0; font-size: 1.25rem; }
  .active { background: #ece9fd; }

  .chat {
    width: 320px;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    height: calc(100vh - 2rem);
    position: sticky;
    top: 1rem;
    border: 1px solid #ddd;
    border-radius: 0.5rem;
    background: #fff;
  }
  .chat-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid #eee;
    font-weight: 600;
  }
  .log {
    flex: 1;
    overflow-y: auto;
    padding: 0.75rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .msg {
    max-width: 85%;
    padding: 0.5rem 0.75rem;
    border-radius: 0.75rem;
    font-size: 0.9rem;
    white-space: pre-wrap;
  }
  .msg.user { align-self: flex-end; background: #ece9fd; }
  .msg.assistant { align-self: flex-start; background: #f4f4f4; }
  .chat-input {
    display: flex;
    gap: 0.25rem;
    padding: 0.5rem;
    border-top: 1px solid #eee;
  }
  .chat-input textarea { flex: 1; resize: none; font: inherit; }

  :global(.tiptap) { outline: none; min-height: 300px; padding: 0.5rem; border: 1px solid #ddd; }
  :global(.tiptap pre) { background: #2e2b29; color: #fff; padding: 0.75rem 1rem; border-radius: 0.5rem; }
</style>
