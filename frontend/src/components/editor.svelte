<script>
  import { onMount } from "svelte";
  import { Editor } from "@tiptap/core";
  import StarterKit from "@tiptap/starter-kit";

  /**
   * @typedef {{ id: string; projectId: string; ownerId: string; title: string }} ManuscriptMeta
   * @typedef {{ id: string; parent_id: string|null; heading: string; body: string; ordinal: number }} Section
   */

  let { id, projectId, ownerId, title: initialTitle, onback } = $props();

  let element;
  let editor = $state.raw(null);
  let tick = $state(0);

  let currentTitle = $state(initialTitle ?? '');
  let saveStatus = $state(/** @type {'idle'|'saving'|'saved'|'error'} */ ('idle'));

  let open = $state(false);
  let messages = $state([]);
  let input = $state("");
  let chatLoading = $state(false);
  let log = $state(/** @type {HTMLElement | undefined} */ (undefined));

  const manuscriptPath = () =>
    `/api/users/${ownerId}/projects/${projectId}/manuscripts/${id}`;

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

  /**
   * Convert manuscript sections to TipTap-compatible HTML.
   * Top-level sections become <h2> headings followed by body paragraphs.
   * Child sections become <h3> headings.
   *
   * @param {Section[]} sections
   * @returns {string}
   */
  function sectionsToHtml(sections) {
    if (!sections || sections.length === 0) return '';

    // Sort top-level by ordinal, then children by ordinal
    const topLevel = sections
      .filter((s) => s.parent_id === null)
      .sort((a, b) => a.ordinal - b.ordinal);

    const children = sections.filter((s) => s.parent_id !== null);

    let html = '';
    for (const section of topLevel) {
      html += `<h2>${escapeHtml(section.heading)}</h2>`;
      if (section.body) html += `<p>${escapeHtml(section.body)}</p>`;

      const subs = children
        .filter((c) => c.parent_id === section.id)
        .sort((a, b) => a.ordinal - b.ordinal);
      for (const sub of subs) {
        html += `<h3>${escapeHtml(sub.heading)}</h3>`;
        if (sub.body) html += `<p>${escapeHtml(sub.body)}</p>`;
      }
    }
    return html;
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  onMount(() => {
    editor = new Editor({
      element,
      extensions: [StarterKit],
      content: '',
      onTransaction: () => tick++,
    });

    // Load the manuscript from the real API
    fetch(manuscriptPath(), {
      headers: { 'Content-Type': 'application/json' },
    })
      .then((r) => r.json())
      .then((doc) => {
        currentTitle = doc.title ?? currentTitle;
        const html = sectionsToHtml(doc.sections ?? []);
        editor.commands.setContent(html || `<p></p>`);
      })
      .catch(() => {
        editor.commands.setContent('<p></p>');
      });

    return () => editor.destroy();
  });

  async function saveTitle() {
    const trimmed = currentTitle.trim();
    if (!trimmed) return;
    saveStatus = 'saving';
    try {
      await fetch(manuscriptPath(), {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: trimmed }),
      });
      saveStatus = 'saved';
      setTimeout(() => (saveStatus = 'idle'), 2000);
    } catch {
      saveStatus = 'error';
    }
  }

  function scrollDown() {
    queueMicrotask(() => log && (log.scrollTop = log.scrollHeight));
  }

  async function send() {
    const text = input.trim();
    if (!text || chatLoading) return;
    messages.push({ role: "user", text });
    input = "";
    chatLoading = true;
    scrollDown();
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          manuscript_id: id,
          message: text,
          document: editor.getText(),
        }),
      });
      if (!res.ok) throw new Error(`${res.status}`);
      const data = await res.json();
      messages.push({ role: "assistant", text: data.reply });
    } catch {
      messages.push({ role: "assistant", text: "Chat not available." });
    }
    chatLoading = false;
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
      <div class="name" role="heading" aria-level="2">
        <input
          class="title-input"
          bind:value={currentTitle}
          onblur={saveTitle}
          aria-label="Manuscript title"
        />
      </div>
      {#each tools as t (t.label)}
        <button
          class:active={t.name && active(t.name, t.attrs)}
          onclick={() => t.run(editor.chain().focus()).run()}
        >
          {t.label}
        </button>
      {/each}
      <button onclick={saveTitle} disabled={saveStatus === 'saving'}>
        {saveStatus === 'saving' ? 'Saving…' : saveStatus === 'saved' ? 'Saved ✓' : 'Save title'}
      </button>
      {#if saveStatus === 'error'}
        <span class="save-error">Save failed</span>
      {/if}
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
        {#each messages as m, i (i)}
          <div class="msg {m.role}">{m.text}</div>
        {/each}
        {#if chatLoading}<div class="msg assistant">…</div>{/if}
      </div>
      <div class="chat-input">
        <textarea
          rows="2"
          placeholder="Ask something…"
          bind:value={input}
          onkeydown={onkey}
        ></textarea>
        <button onclick={send} disabled={chatLoading}>Send</button>
      </div>
    </aside>
  {/if}
</div>

<style>
  .layout { display: flex; gap: 1rem; align-items: flex-start; }
  .main { flex: 1; min-width: 0; }
  .bar { display: flex; gap: 0.25rem; flex-wrap: wrap; align-items: center; margin-bottom: 1rem; }
  .name { width: 100%; margin: 0.5rem 0; font-size: 1.25rem; display: flex; }
  .title-input {
    font: inherit;
    font-size: 1.25rem;
    font-weight: 600;
    border: none;
    border-bottom: 2px solid transparent;
    background: transparent;
    flex: 1;
    padding: 0.1rem 0.25rem;
    outline: none;
    transition: border-color 0.15s;
  }
  .title-input:focus { border-bottom-color: #2b5fd9; }
  .save-error { color: #c0392b; font-size: 0.85rem; align-self: center; }
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

  :global(.tiptap) { outline: none; min-height: 300px; padding: 0.5rem; border: 1px solid #ddd; border-radius: 6px; }
  :global(.tiptap pre) { background: #2e2b29; color: #fff; padding: 0.75rem 1rem; border-radius: 0.5rem; }
</style>
