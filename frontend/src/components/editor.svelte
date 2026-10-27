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

  // Revision history panel
  let historyOpen = $state(false);
  let revisions = $state([]);
  let historyLoading = $state(false);
  let historyError = $state("");
  let restoringId = $state(null);

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

    // Ensure a revision history exists for this manuscript (idempotent – 409 means already exists)
    fetch("/api/revision-histories", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        project_id: projectId,
        manuscript_id: id,
        tree_hash: JSON.stringify({ section_id: null, heading: null, body: null }),
        message: "Initial revision",
      }),
    }).catch(() => {});

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

    // Commit a new revision on save (best-effort; ignore failures)
    // tree_hash encodes the full section snapshot so restore can replay it
    const snapshot = JSON.stringify({ section_id: selectedId, heading, body });
    fetch(`/api/revision-histories/${id}/revisions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        branch_name: "main",
        tree_hash: snapshot,
        message: `Saved section "${heading}"`,
      }),
    })
      .then((r) => {
        if (r.ok && historyOpen) loadRevisions();
      })
      .catch(() => {});
  }

  // ---------------------------------------------------------------------------
  // Revision history
  // ---------------------------------------------------------------------------

  async function loadRevisions() {
    historyLoading = true;
    historyError = "";
    try {
      const res = await fetch(`/api/revision-histories/${id}/revisions`);
      if (res.status === 404) {
        revisions = [];
      } else if (!res.ok) {
        historyError = "Failed to load revision history.";
      } else {
        revisions = await res.json();
      }
    } catch {
      historyError = "Failed to load revision history.";
    }
    historyLoading = false;
  }

  function toggleHistory() {
    historyOpen = !historyOpen;
    if (historyOpen && revisions.length === 0 && !historyLoading) {
      loadRevisions();
    }
  }

  async function restoreRevision(revisionId) {
    if (restoringId) return;
    restoringId = revisionId;
    try {
      const res = await fetch(`/api/revision-histories/${id}/revisions/restore`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          branch_name: "main",
          target_revision_id: revisionId,
          message: "Restored via revision history",
        }),
      });
      if (!res.ok) return;

      const revision = await res.json();

      // Parse the snapshot stored in tree_hash to recover section content
      let snapshot = null;
      try { snapshot = JSON.parse(revision.tree_hash); } catch { /* legacy revisions without JSON snapshot */ }

      if (snapshot?.section_id && snapshot?.heading != null && snapshot?.body != null) {
        // Write the old content back to the backend
        await fetch(
          `/api/users/${ownerId}/projects/${projectId}/manuscripts/${id}/sections/${snapshot.section_id}`,
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ heading: snapshot.heading, body: snapshot.body }),
          }
        );
        // Always update local state and the editor — the revision was created
        // successfully even if the PATCH above had a transient failure.
        sections = sections.map((s) =>
          s.id === snapshot.section_id ? { ...s, heading: snapshot.heading, body: snapshot.body } : s
        );
        // If the restored section is currently open, refresh the editor.
        // Pass emitUpdate:true so TipTap replaces the document even when the
        // HTML string is identical to the current content.
        if (selectedId === snapshot.section_id) {
          heading = snapshot.heading;
          editor.commands.setContent(snapshot.body ?? "", true);
        }
      }

      await loadRevisions();
    } finally {
      restoringId = null;
    }
  }

  function shortId(uuid) {
    return uuid.slice(0, 8);
  }

  // ---------------------------------------------------------------------------
  // Chat
  // ---------------------------------------------------------------------------

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
      <button class:active={historyOpen} onclick={toggleHistory}>History</button>
      <button class:active={open} onclick={() => (open = !open)}>Chat</button>
    </div>

    <input class="heading" bind:value={heading} placeholder="Section heading" disabled={!selectedId} />
    <div bind:this={element}></div>
  </div>

  {#if historyOpen}
    <aside class="history">
      <div class="side-head">
        <span>Revision History</span>
        <button class="close-btn" onclick={() => (historyOpen = false)}>✕</button>
      </div>

      {#if historyLoading}
        <div class="history-msg">Loading…</div>
      {:else if historyError}
        <div class="history-msg error">{historyError}</div>
      {:else if revisions.length === 0}
        <div class="history-msg">No revisions yet. Save to create one.</div>
      {:else}
        <ul class="rev-list">
          {#each revisions as rev (rev.id)}
            <li class="rev-item">
              <div class="rev-id" title={rev.id}>#{shortId(rev.id)}</div>
              <div class="rev-msg">{rev.message}</div>
              {#if rev.parent_ids.length > 0}
                <div class="rev-parents">
                  parent{rev.parent_ids.length > 1 ? "s" : ""}:
                  {rev.parent_ids.map(shortId).join(", ")}
                </div>
              {/if}
              <button
                class="restore-btn"
                disabled={restoringId === rev.id}
                onclick={() => restoreRevision(rev.id)}
              >
                {restoringId === rev.id ? "Restoring…" : "Restore"}
              </button>
            </li>
          {/each}
        </ul>
      {/if}

      <div class="history-footer">
        <button onclick={loadRevisions} disabled={historyLoading}>↻ Refresh</button>
      </div>
    </aside>
  {/if}

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
  .side-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid #eee;
    font-weight: 600;
  }
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

  /* Revision history panel */
  .history {
    width: 260px;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    max-height: calc(100vh - 2rem);
    position: sticky;
    top: 1rem;
    border: 1px solid #ddd;
    border-radius: 0.5rem;
    background: #fff;
    color: #000;
  }
  .close-btn {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 0.9rem;
    padding: 0;
    color: #666;
  }
  .close-btn:hover { color: #000; }
  .history-msg {
    padding: 0.75rem;
    color: #666;
    font-size: 0.875rem;
  }
  .history-msg.error { color: #c00; }
  .rev-list {
    flex: 1;
    overflow-y: auto;
    list-style: none;
    margin: 0;
    padding: 0.25rem 0;
  }
  .rev-item {
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid #f0f0f0;
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }
  .rev-item:last-child { border-bottom: none; }
  .rev-id {
    font-family: monospace;
    font-size: 0.75rem;
    color: #888;
  }
  .rev-msg {
    font-size: 0.875rem;
    color: #222;
    word-break: break-word;
  }
  .rev-parents {
    font-family: monospace;
    font-size: 0.7rem;
    color: #aaa;
  }
  .restore-btn {
    align-self: flex-start;
    margin-top: 0.25rem;
    padding: 0.2rem 0.6rem;
    font-size: 0.8rem;
    border: 1px solid #ddd;
    border-radius: 0.3rem;
    background: #f9f9f9;
    cursor: pointer;
  }
  .restore-btn:hover:not(:disabled) { background: #ece9fd; border-color: #c4b5fd; }
  .restore-btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .history-footer {
    padding: 0.5rem 0.75rem;
    border-top: 1px solid #eee;
  }
  .history-footer button {
    font-size: 0.8rem;
    padding: 0.2rem 0.5rem;
    border: 1px solid #ddd;
    border-radius: 0.3rem;
    background: #f9f9f9;
    cursor: pointer;
  }
  .history-footer button:hover:not(:disabled) { background: #f0f0f0; }
  .history-footer button:disabled { opacity: 0.5; cursor: not-allowed; }

  /* Chat panel */
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
