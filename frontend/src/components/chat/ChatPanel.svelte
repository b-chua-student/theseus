<script>
  import { startConversation, askConversation, listConversations, getConversation, listIndexedSourceIds } from "../../lib/api/chat.js";
  import ContextDropdown from "./ContextDropdown.svelte";
  import { encodeSelection, initialSelection, restoreSelection } from "./contextSelection.js";
  import { tick as flushUI } from "svelte";
  import { marked } from "marked";
  import DOMPurify from "dompurify";
  // `notice` is write-only here: the parent (editor.svelte) binds it and displays it.
  // eslint-disable-next-line no-useless-assignment
  let { projectId, editor, tick, open, onclose, notice = $bindable() } = $props();

  // Keep this component mounted while closed to retain the session conversation.
  // One conversation continues across context changes; the selection is read at send time.
  let selection = $state(initialSelection());
  // Saved sources that can no longer be searched, named when a chat is reopened.
  let unavailableSources = $state([]);
  let conversationId = $state(null);
  let messages = $state([]);
  let savedConversations = $state([]);
  let historyLoading = $state(false);
  let historyError = $state('');
  let loadedProject = $state(null);
  let historyRequest = 0;

  $effect(() => {
    const id = projectId;
    if (id !== loadedProject) {
      loadedProject = id;
      conversationId = null;
      messages = [];
      savedConversations = [];
      selection = initialSelection();
      unavailableSources = [];
      refreshHistory(id);
    }
  });

  async function refreshHistory(id = projectId) {
    const request = ++historyRequest;
    historyLoading = true;
    historyError = '';
    try {
      const conversations = await listConversations(id);
      if (request === historyRequest) savedConversations = conversations;
    } catch (e) {
      if (request === historyRequest) historyError = e.message;
    } finally {
      if (request === historyRequest) historyLoading = false;
    }
  }

  async function openConversation(id) {
    if (!id || loading) return;
    const project = projectId;
    loading = true;
    historyError = '';
    try {
      const conversation = await getConversation(project, id);
      if (project !== projectId) return;
      // The indexed sources show which saved sources are gone, and fill in an old all-library
      // record that has no source list. If they can't be loaded, the saved choices are kept.
      const indexedIds = await listIndexedSourceIds(project).catch(() => null);
      if (project !== projectId) return;
      const restored = restoreSelection(conversation, indexedIds);
      selection = restored.selection;
      unavailableSources = restored.unavailable;
      conversationId = id;
      messages = conversation.exchanges.flatMap(e => [
        { id: nextMessageId++, role: 'user', text: e.query, timestamp: e.asked_at },
        { id: nextMessageId++, role: 'assistant', text: e.answer, timestamp: e.asked_at },
      ]);
      input = '';
      selectionQuote = '';
      scrollDown();
    } catch (e) { historyError = e.message; }
    finally { loading = false; }
  }

  function newConversation() {
    conversationId = null;
    messages = [];
    selection = initialSelection();
    unavailableSources = [];
    input = '';
    selectionQuote = '';
  }

  let nextMessageId = 0;
  let input = $state("");
  let loading = $state(false);
  let log = $state();


  // Browser-local timestamps and writing tools.
  const hasSelection = $derived.by(() => {
    tick;
    return !!editor && !editor.state.selection.empty;
  });
  let composer = $state();
  let selectionQuote = $state('');
  const formatTime = (value) => new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  // The assistant's reply is untrusted text, so parse it as markdown and sanitize
  // the resulting HTML before it is ever assigned with {@html}. User messages are
  // rendered as plain text (see the template), so they are never run through this.
  marked.setOptions({ breaks: true });
  // Open links from replies in a new tab so they never replace the editor.
  DOMPurify.addHook('afterSanitizeAttributes', (node) => {
    if (node.tagName === 'A' && node.getAttribute('href')) {
      node.setAttribute('target', '_blank');
      node.setAttribute('rel', 'noopener noreferrer');
    }
  });
  function renderMarkdown(text) {
    return DOMPurify.sanitize(marked.parse(text ?? '', { async: false }), { ADD_ATTR: ['target'] });
  }
  const fullTime = (value) => new Date(value).toLocaleString();
  const prompts = [
    { label: 'Paraphrase academically', text: 'Paraphrase the selected passage or current manuscript in an academic tone.' },
    { label: 'Summarize manuscript', text: 'Summarize the current manuscript in one concise paragraph.' },
    { label: 'Critique methodology', text: 'Review the methodology in the current manuscript and identify areas to improve.' },
  ];
  function fillPrompt(text) { input = text; composer?.focus(); }
  function writingTool(event) {
    const choice = event.currentTarget.value;
    if (choice) fillPrompt(choice);
    event.currentTarget.value = '';
  }
  function quoteSelection() {
    if (!editor) return;
    const { from, to } = editor.state.selection;
    selectionQuote = editor.state.doc.textBetween(from, to, '\n').trim();
    if (!selectionQuote) notice = 'Select a passage in the manuscript, then choose Quote selection.';
    else composer?.focus();
  }
  async function copyReply(text) {
    try { await navigator.clipboard.writeText(text); notice = 'Reply copied.'; }
    catch { notice = 'Copy is unavailable. Select the reply text and copy manually.'; }
  }
  function insertReply(text) {
    if (!editor || !text) return;
    // Treat generated text as plain text, never raw HTML. Existing Save persists it.
    const paragraphs = text.split(/\n\n+/).map(line => ({
      type: 'paragraph', content: line ? [{ type: 'text', text: line }] : [],
    }));
    editor.chain().focus().insertContent(paragraphs).run();
    notice = 'Reply inserted at the manuscript cursor. Review the text and save your changes.';
  }

  function scrollDown() {
    flushUI().then(() => { if (log) log.scrollTop = log.scrollHeight; });
  }

  // Failures worth offering a retry for: network errors (no status), rate limits,
  // AI provider errors and an unavailable assistant. Validation errors (4xx) won't
  // succeed on retry, so they are not retryable.
  const isRetryable = (e) => !e.status || e.status === 429 || e.status >= 500;

  async function ask(text, quote) {
    // Read the selection and the draft now, as they are when the writer asks.
    const { contextScope, sourceIds, manuscriptText, web, manuscript } = encodeSelection(selection, editor?.getText() ?? "");
    const checked = { web, manuscript };
    if (!conversationId) {
      conversationId = await startConversation(projectId);
    }
    try {
      return await askConversation(projectId, conversationId, text, contextScope, sourceIds, manuscriptText, quote, checked);
    } catch (e) {
      // The conversation is gone (e.g. the server restarted): start a fresh one once.
      if (e.status === 404 && e.code === "assistant.conversation_not_found") {
        conversationId = await startConversation(projectId);
        return await askConversation(projectId, conversationId, text, contextScope, sourceIds, manuscriptText, quote, checked);
      }
      throw e;
    }
  }

  async function send(retryText, retryQuote = null) {
    // `retryText` is only a string when called from the Retry button; the click
    // handler otherwise passes an event.
    const retry = typeof retryText === "string";
    const text = retry ? retryText : input.trim();
    if (!text || loading) return;
    // The quote travels as its own field, exactly as selected, never inside the question.
    const quote = retry ? retryQuote : selectionQuote || null;
    if (!retry) {
      messages.push({ id: nextMessageId++, role: "user", text, quote, timestamp: Date.now() });
      input = "";
      selectionQuote = "";
    }
    loading = true;
    scrollDown();
    try {
      const { answer, citations } = await ask(text, quote);
      messages.push({ id: nextMessageId++, role: "assistant", text: answer, citations, timestamp: Date.now() });
      refreshHistory();
    } catch (e) {
      messages.push({
        id: nextMessageId++,
        role: "assistant",
        text: e.message || "Request failed. Please check the backend connection and retry.",
        timestamp: Date.now(),
        isError: true,
        retryText: isRetryable(e) ? text : null,
        retryQuote: quote,
      });
    }
    loading = false;
    scrollDown();
  }

  // Remove the failed reply and resend the question that caused it.
  function retryMessage(m) {
    const index = messages.indexOf(m);
    if (index !== -1) messages.splice(index, 1);
    send(m.retryText, m.retryQuote);
  }

  function onkey(e) {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      send();
    }
  }
</script>

{#snippet icon(name, size = 14)}
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    {#if name === 'panel'}<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M15 3v18"/>
    {:else if name === 'send'}<path d="m22 2-7 20-4-9-9-4 20-7ZM22 2 11 13"/>{/if}
  </svg>
{/snippet}
    {#if open}
      <aside class="chat scholar-chat" id="theseus-chat" aria-label="Theseus AI assistant">
        <header class="scholar-header">
          <div class="scholar-identity"><span class="scholar-avatar" aria-hidden="true">t<span></span></span><div><h3>Theseus Scholar AI</h3></div></div>
          <button type="button" class="scholar-close" onclick={onclose} aria-label="Close assistant" title="Close assistant">{@render icon('panel')}</button>
        </header>

        <div class="conversation-history">
          <label for="saved-conversations">Saved conversations</label>
          <select id="saved-conversations" value={conversationId ?? ''} disabled={loading || historyLoading} onchange={(event) => openConversation(event.currentTarget.value)}>
            <option value="">{historyLoading ? 'Loading conversations…' : 'Choose a conversation'}</option>
            {#each savedConversations as conversation (conversation.id)}
              <option value={conversation.id}>{conversation.title}</option>
            {/each}
          </select>
          <button type="button" disabled={loading} onclick={newConversation}>New chat</button>
          <button type="button" disabled={historyLoading || loading} onclick={() => refreshHistory()}>Refresh</button>
          {#if historyError}<p role="alert">{historyError}</p>
          {:else if !historyLoading && savedConversations.length === 0}<p>No saved conversations yet.</p>{/if}
        </div>
        <ContextDropdown {projectId} bind:selection manuscriptAvailable={!!editor} />
        {#each unavailableSources as source (source.id)}
          <p class="scholar-unavailable" role="status">{source.title} is unavailable and was left out of the selection.</p>
        {/each}
        {#if messages.length === 0}
        <!-- LOCAL ONLY: quick prompts fill the composer. They do not send requests. -->
        <div class="scholar-prompts" aria-label="Suggested prompts">{#each prompts as prompt (prompt.label)}<button type="button" onclick={() => fillPrompt(prompt.text)}><span aria-hidden="true">✧</span>{prompt.label}</button>{/each}</div>
        {/if}
        <div class="log scholar-log" bind:this={log} role="log" aria-live="polite" aria-label="Assistant conversation">
          {#if messages.length === 0}
            <div class="scholar-welcome"><span class="welcome-label">YOUR WRITING SPACE</span><h4>Let’s work on your manuscript.</h4><p>Ask for a summary, rephrase a passage, or review your writing.</p><span class="welcome-note">Review AI suggestions before using them.</span></div>
          {/if}
          {#each messages as m (m.id)}
            <article class="scholar-message" class:from-user={m.role === 'user'} class:reply-error={m.isError}>
              <div class="scholar-message-meta"><span>{#if m.role === 'assistant'}<span class="tiny-avatar" aria-hidden="true">t</span>Theseus AI <span class="reply-type">{m.isError ? 'Request issue' : 'Writing assistant'}</span>{:else}You{/if}</span><time datetime={new Date(m.timestamp).toISOString()} title={fullTime(m.timestamp)}>{formatTime(m.timestamp)}</time></div>
              {#if m.role === 'assistant' && !m.isError}
                <!-- renderMarkdown() sanitizes the HTML with DOMPurify before it is rendered. -->
                <!-- eslint-disable-next-line svelte/no-at-html-tags -->
                <div class="scholar-bubble markdown-body">{@html renderMarkdown(m.text)}</div>
                {#if m.citations?.length}
                  <ul class="scholar-citations" aria-label="Sources cited">
                    {#each m.citations as citation (citation.key)}<li>[{citation.key}] {citation.title || "Untitled source"}{citation.location ? ` (${citation.location})` : ""}</li>{/each}
                  </ul>
                {/if}
              {:else}
                <div class="scholar-bubble">{#if m.quote}<blockquote class="scholar-quote">{m.quote}</blockquote>{/if}{m.text}</div>
              {/if}
              {#if m.isError && m.retryText}<div class="scholar-reply-actions"><button type="button" onclick={() => retryMessage(m)} disabled={loading}>Try again</button></div>{/if}
              {#if m.role === 'assistant' && !m.isError}<div class="scholar-reply-actions"><button type="button" onclick={() => copyReply(m.text)}>Copy</button><button type="button" onclick={() => insertReply(m.text)} disabled={!editor}>Use in manuscript</button></div>{/if}
            </article>
          {/each}
          {#if loading}<div class="scholar-thinking" role="status"><span class="tiny-avatar" aria-hidden="true">t</span>Theseus is thinking<span class="thinking-dots" aria-hidden="true">…</span></div>{/if}
        </div>
        <div class="scholar-composer-area">
          {#if selectionQuote}<div class="scholar-selection"><span class="selection-tag">QUOTED</span><span class="selection-excerpt" title={selectionQuote}>{selectionQuote}</span><button type="button" onclick={() => selectionQuote = ''} aria-label="Dismiss selected passage">×</button></div>{/if}
          <div class="scholar-composer-tools"><select aria-label="Writing tools" onchange={writingTool}><option value="">Writing tools</option><option value="Rewrite the current manuscript passage in a formal academic tone.">Academic tone</option><option value="Explain the current manuscript in clear, concise language.">Clear and concise</option><option value="Review the current manuscript for structure, clarity, and unsupported claims.">Review writing</option></select>
            {#if hasSelection && !selectionQuote}<button type="button" onclick={quoteSelection}>Quote selection</button>{/if}
            <!-- TODO(API): Source picker, citation lookup, and source verification need
                 real project sources. No sources or verification badges are fabricated. -->
            <button type="button" disabled title="Source lookup is not connected">Cite source</button>
          </div>
          <div class="scholar-input"><textarea bind:this={composer} rows="3" placeholder="Ask Theseus to rephrase, summarize, or review your manuscript…" aria-label="Message the assistant" bind:value={input} onkeydown={onkey}></textarea><button type="button" class="scholar-send" onclick={() => send()} disabled={loading || !editor || !input.trim()} aria-label="Send message" title="Send message">{@render icon('send', 16)}</button></div>
          <div class="scholar-input-hint"><span>Enter to send · Shift + Enter for a new line</span><span>AI suggestions</span></div>
        </div>
      </aside>
    {/if}

<style>
  .conversation-history { padding: 10px 14px; border-bottom: 1px solid var(--border); display: flex; flex-wrap: wrap; gap: 6px; }
  .conversation-history label, .conversation-history p { width: 100%; font-size: 11px; margin: 0; }
  .conversation-history select { width: 100%; min-width: 0; }
  .conversation-history button, .conversation-history select { padding: 6px; border: 1px solid var(--border); border-radius: 5px; background: var(--surface); color: inherit; }

  .scholar-chat, .scholar-chat * { box-sizing: border-box; }
  button, select, textarea { font: inherit; color: inherit; margin: 0; }
  button { display: inline-flex; align-items: center; justify-content: center; gap: 6px; cursor: pointer; line-height: 1.3; }
  button:disabled, select:disabled { cursor: default; opacity: 1; -webkit-text-fill-color: currentColor; }
  button:not(:disabled):hover { background: #e9ede9; }
  button:focus-visible, select:focus-visible, textarea:focus-visible { outline: 2px solid var(--green); outline-offset: 2px; }
  .chat.scholar-chat { width: 370px; min-width: 0; flex-shrink: 0; display: flex; flex-direction: column; min-height: 0; background: var(--surface); border-left: 1px solid var(--border); font-family: var(--sans); }
  .scholar-header { display: flex; align-items: center; justify-content: space-between; padding: 14px 14px 10px; gap: 10px; }
  .scholar-identity { display: flex; gap: 9px; align-items: center; min-width: 0; }.scholar-identity > div { min-width: 0; }.scholar-identity h3 { font-family: var(--sans); font-size: 15px; font-weight: 600; text-transform: none; letter-spacing: 0; margin: 0 0 3px; }
  .scholar-avatar { display: grid; place-items: center; width: 29px; height: 29px; border-radius: 10px; background: var(--accent); color: white; font: 600 17px var(--sans); flex-shrink: 0; position: relative; }.scholar-avatar > span { position: absolute; width: 7px; height: 7px; background: #bed1cb; border: 2px solid var(--surface); border-radius: 50%; right: -2px; top: 0; }.scholar-close { background: transparent; border: 0; padding: 3px; color: var(--text-muted); }

  .scholar-prompts { display: flex; gap: 5px; overflow-x: auto; padding: 9px 12px; background: var(--surface-muted); border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); scrollbar-width: thin; flex-shrink: 0; }.scholar-prompts button { white-space: nowrap; border: 1px solid #c9d5cc; border-radius: 999px; background: #e7eee8; color: var(--accent); padding: 5px 9px; font-size: 9px; font-weight: 500; }.scholar-prompts button span { color: var(--accent); }
  .scholar-composer-tools select { max-width: 145px; padding: 4px 5px; border: 1px solid var(--border); border-radius: 4px; background: var(--surface); color: var(--text); font: 9px var(--sans); }
  .scholar-log { flex: 1; min-height: 0; overflow-y: auto; overscroll-behavior: contain; padding: 17px 12px; display: flex; flex-direction: column; gap: 19px; scrollbar-width: thin; scrollbar-color: #bac9be transparent; }
  .scholar-welcome { margin: auto 0; padding: 24px 18px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface-muted); }.welcome-label { font: 8px var(--mono); letter-spacing: .06em; color: var(--accent); }.scholar-welcome h4 { font: 600 19px/1.3 var(--sans); margin: 10px 0; }.scholar-welcome p { font-size: 11px; line-height: 1.7; color: var(--text-muted); margin: 0 0 18px; }.welcome-note { font: 8px/1.5 var(--mono); color: var(--text-muted); }
  .scholar-message { min-width: 0; width: 100%; }.scholar-message.from-user { width: 88%; align-self: flex-end; }.scholar-message-meta { display: flex; align-items: center; justify-content: space-between; gap: 6px; color: var(--text-muted); font-size: 9px; margin: 0 2px 6px; }.scholar-message-meta > span { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }.scholar-message-meta time { white-space: nowrap; font: 7.5px var(--mono); }.from-user .scholar-message-meta { justify-content: flex-end; }.tiny-avatar { display: inline-grid; place-items: center; width: 15px; height: 15px; border-radius: 5px; background: var(--accent); color: white; font: 10px var(--sans); flex-shrink: 0; }.reply-type { font: 7px var(--mono); background: #e5ece5; padding: 2px 4px; border-radius: 3px; color: var(--accent); }
  .scholar-bubble { white-space: pre-wrap; overflow-wrap: anywhere; padding: 13px 12px; background: white; border: 1px solid #cbd6cd; border-radius: 3px 13px 13px 13px; font-size: 11px; line-height: 1.75; color: var(--text); }
  .markdown-body { white-space: normal; }
  .markdown-body :global(p) { margin: 0 0 8px; }
  .markdown-body :global(p:last-child) { margin-bottom: 0; }
  .markdown-body :global(ul), .markdown-body :global(ol) { margin: 0 0 8px; padding-left: 18px; }
  .markdown-body :global(li) { margin: 2px 0; }
  .markdown-body :global(code) { background: #eef1ee; border-radius: 3px; padding: 1px 4px; font-family: var(--mono); font-size: 10px; }
  .markdown-body :global(pre) { background: #eef1ee; border-radius: 6px; padding: 8px 10px; overflow-x: auto; margin: 0 0 8px; }
  .markdown-body :global(pre code) { background: none; padding: 0; }
  .markdown-body :global(blockquote) { margin: 0 0 8px; padding-left: 10px; border-left: 2px solid #cbd6cd; color: var(--text-muted); }
  .markdown-body :global(h1), .markdown-body :global(h2), .markdown-body :global(h3) { margin: 0 0 6px; line-height: 1.3; }
  .markdown-body :global(a) { color: var(--accent); text-decoration: underline; }
  .markdown-body :global(table) { border-collapse: collapse; margin: 0 0 8px; }
  .markdown-body :global(th), .markdown-body :global(td) { border: 1px solid #cbd6cd; padding: 3px 7px; }.from-user .scholar-bubble { border: 0; background: var(--accent); color: white; border-radius: 13px 13px 3px 13px; line-height: 1.6; }.reply-error .scholar-bubble { background: #fcf6ef; border-color: #dfcdb8; }.scholar-reply-actions { display: flex; justify-content: flex-end; gap: 6px; margin-top: 6px; }.scholar-reply-actions button { font-size: 8px; padding: 4px 6px; border: 1px solid var(--border); border-radius: 4px; background: var(--surface-muted); color: var(--accent); }
  .scholar-thinking { display: flex; align-items: center; gap: 6px; font-size: 10px; color: var(--text-muted); padding: 4px 0; }.thinking-dots { animation: scholar-pulse 1s ease-in-out infinite; }@keyframes scholar-pulse { 50% { opacity: .3; } }
  .scholar-composer-area { flex-shrink: 0; border-top: 1px solid var(--border); background: var(--surface-muted); padding: 10px; }.scholar-selection { display: flex; gap: 6px; align-items: center; padding: 7px 0 9px; min-width: 0; border-bottom: 1px solid var(--border); margin-bottom: 8px; }.selection-tag { font: 7px var(--mono); background: var(--accent); color: white; padding: 3px; border-radius: 3px; }.selection-excerpt { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 9px; flex: 1; min-width: 0; font-style: italic; }.scholar-selection button { border: 1px solid var(--border); background: var(--surface); border-radius: 4px; font-size: 8px; padding: 3px 5px; }
  .scholar-composer-tools { display: flex; align-items: center; gap: 5px; margin-bottom: 7px; flex-wrap: wrap; }.scholar-composer-tools button { border: 1px solid var(--border); border-radius: 4px; background: var(--surface); font: 8px var(--mono); padding: 4px 5px; }.scholar-composer-tools button:disabled { color: #8b968f; }
  .scholar-input { position: relative; border: 1px solid #bdccbf; border-radius: 15px; background: var(--paper); padding: 10px; display: flex; align-items: flex-end; gap: 7px; }.scholar-input:focus-within { border-color: var(--accent); box-shadow: 0 0 0 2px #3b5b4f12; }.scholar-input textarea { width: 100%; min-width: 0; flex: 1; resize: vertical; max-height: 180px; min-height: 56px; border: 0; background: transparent; font: 11px/1.6 var(--sans); color: var(--text); outline: none; }.scholar-input textarea::placeholder { color: #87948a; }.scholar-send { display: flex; align-items: center; justify-content: center; width: 31px; height: 31px; flex-shrink: 0; padding: 0; background: var(--accent); color: white; border: 0; border-radius: 10px; }.scholar-send:not(:disabled):hover { background: var(--accent-hover); }.scholar-send:disabled { opacity: .45; cursor: default; }.scholar-input-hint { display: flex; justify-content: space-between; gap: 5px; color: var(--text-muted); font-size: 7px; margin: 6px 3px 0; }
  @media (max-width: 1023px) { .chat.scholar-chat { width: 100%; height: 600px; border-left: 0; border-top: 1px solid var(--border); } }
  .scholar-unavailable { margin: 6px 14px 0; font-size: 10px; color: var(--text-muted); overflow-wrap: anywhere; }
  .scholar-citations { list-style: none; margin: 6px 2px 0; padding: 0; font: 9px var(--mono); color: var(--text-muted); overflow-wrap: anywhere; }
  .scholar-quote { margin: 0 0 6px; padding: 2px 0 2px 8px; border-left: 2px solid currentColor; opacity: .8; white-space: pre-wrap; }
  @media (prefers-reduced-motion: reduce) { .thinking-dots { animation: none; } }
</style>
