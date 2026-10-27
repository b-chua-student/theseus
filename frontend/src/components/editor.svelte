<script>
  import { onMount } from "svelte";
  import { Editor } from "@tiptap/core";
  import StarterKit from "@tiptap/starter-kit";

  let { id, projectId, ownerId, onback } = $props();

  let element;
  let editor = $state.raw(null);
  let tick = $state(0);

  let title = $state("");
  let sections = $state([]);
  let selectedId = $state(null);
  let heading = $state("");

  let open = $state(false);
  let messages = $state([]);
  let input = $state("");
  let loading = $state(false);
  let log;

  const active = (name, attrs) => (tick, editor?.isActive(name, attrs));

  const rows = $derived.by(() => {
    const byParent = {};
    for (const s of sections) (byParent[s.parent_id ?? "root"] ??= []).push(s);
    const out = [];
    const walk = (parent, depth) => {
      const children = (byParent[parent] ?? []).sort((a, b) => a.ordinal - b.ordinal);
      for (const s of children) {
        out.push({ ...s, depth });
        walk(s.id, depth + 1);
      }
    };
    walk("root", 0);
    return out;
  });

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

    fetch(`/api/users/${ownerId}/projects/${projectId}/manuscripts/${id}`)
      .then((r) => r.json())
      .then((m) => {
        title = m.title;
        sections = m.sections ?? [];
        if (rows.length) select(rows[0].id);
      });

    return () => editor.destroy();
  });

  function select(sectionId) {
    const s = sections.find((x) => x.id === sectionId);
    if (!s) return;
    selectedId = s.id;
    heading = s.heading;
    editor.commands.setContent(s.body ?? "");
  }

  async function save() {
    if (!selectedId) return;
    const body = editor.getHTML();
    const res = await fetch(`/api/users/${ownerId}/projects/${projectId}/manuscripts/${id}/sections/${selectedId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ heading, body }),
    });
    if (!res.ok) return;
    sections = sections.map((s) => (s.id === selectedId ? { ...s, heading, body } : s));
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
          manuscript_id: id,
          section_id: selectedId,
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
  <aside class="sections">
    <div class="side-head">Sections</div>
    <ul>
      {#each rows as s (s.id)}
        <li>
          <button
            class="section"
            class:active={s.id === selectedId}
            style="padding-left: {0.5 + s.depth * 1}rem"
            onclick={() => select(s.id)}
          >
            {s.heading}
          </button>
        </li>
      {:else}
        <li class="empty">No sections</li>
      {/each}
    </ul>
  </aside>

  <div class="main">
    <div class="bar">
      <button onclick={onback}>← Back</button>
      <h2 class="name">{title}</h2>
      {#each tools as t (t.label)}
        <button
          class:active={t.name && active(t.name, t.attrs)}
          onclick={() => t.run(editor.chain().focus()).run()}
        >
          {t.label}
        </button>
      {/each}
      <button onclick={save} disabled={!selectedId}>Save</button>
      <button class:active={open} onclick={() => (open = !open)}>Chat</button>
    </div>

    <input class="heading" bind:value={heading} placeholder="Section heading" disabled={!selectedId} />
    <div bind:this={element}></div>
  </div>

  {#if open}
    <aside class="chat">
      <div class="chat-head">
        <span>Assistant</span>
        <button onclick={() => (open = false)}>✕</button>
      </div>
      <div class="log" bind:this={log}>
        {#each messages as m}
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
  .heading { width: 100%; box-sizing: border-box; margin-bottom: 0.5rem; padding: 0.5rem; font: inherit; font-weight: 600; }

  .sections {
    width: 240px;
    flex-shrink: 0;
    position: sticky;
    top: 1rem;
    max-height: calc(100vh - 2rem);
    overflow-y: auto;
    border: 1px solid #ddd;
    border-radius: 0.5rem;
    background: #fff;
    color: #000;
  }
  .side-head { padding: 0.5rem 0.75rem; border-bottom: 1px solid #eee; font-weight: 600; }
  .sections ul { list-style: none; margin: 0; padding: 0.25rem 0; }
  .section {
    display: block;
    width: 100%;
    text-align: left;
    border: none;
    background: none;
    padding: 0.4rem 0.5rem;
    cursor: pointer;
    color: #000;
  }
  .section:hover { background: #f5f5f5; }
  .section.active { background: #ece9fd; }
  .empty { padding: 0.5rem 0.75rem; color: #888; }

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
