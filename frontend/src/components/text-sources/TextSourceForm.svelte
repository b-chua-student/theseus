<script>
  /**
   * Create/edit form for a text source.
   *
   * Props:
   *  - projectId: scopes the draft key and every API call
   *  - source: existing TextSource (detail DTO) → edit mode; omit for create
   *  - onsaved(source): called with the saved DTO
   *  - oncancel(): called when the user cancels
   *
   * User content is only ever rendered as text (never {@html}).
   */
  import { untrack, tick } from 'svelte';
  import {
    createTextSource,
    updateTextSource,
    TextSourceValidationError,
  } from '../../lib/api/textSources.js';

  const LIMITS = {
    title: 200,
    description: 1000,
    content: 100000,
    tags: 10,
  };
  const DRAFT_DEBOUNCE_MS = 1000;
  const CONTENT_TYPES = ['documentation', 'notes', 'code', 'other'];

  /** @type {{projectId: string, source?: any, modal?: boolean, onsaved?: (s: any) => void, oncancel?: () => void}} */
  let { projectId, source = null, modal = false, onsaved, oncancel } = $props();

  const initial = untrack(() => source);
  const editing = initial !== null && initial !== undefined;
  const draftKey = untrack(
    () => `theseus:text-draft:${projectId}${editing ? `:${initial.id}` : ''}`,
  );

  /** @returns {any|null} */
  function loadDraft() {
    try {
      const raw = localStorage.getItem(draftKey);
      const d = raw ? JSON.parse(raw) : null;
      return d && typeof d === 'object' ? d : null;
    } catch {
      return null;
    }
  }

  const draft = loadDraft();
  const base = draft ?? {
    title: initial?.title ?? '',
    description: initial?.description ?? '',
    tags: (initial?.tags ?? []).join(', '),
    contentType: initial?.contentType ?? 'other',
    content: initial?.content ?? '',
  };
  const str = (v, fallback = '') => (typeof v === 'string' ? v : fallback);

  let title = $state(str(base.title));
  let description = $state(str(base.description));
  let tagsText = $state(str(base.tags));
  let contentType = $state(CONTENT_TYPES.includes(base.contentType) ? base.contentType : 'other');
  let content = $state(str(base.content));
  let restored = $state(draft !== null);
  let showPreview = $state(false);
  let submitting = $state(false);
  /** @type {Record<string, string>} */
  let errors = $state({});
  let formError = $state('');

  /** Trim, drop blanks, dedupe (case-sensitive), same as the backend. */
  function parseTags(text) {
    return [
      ...new Set(
        text
          .split(',')
          .map((t) => t.trim())
          .filter(Boolean),
      ),
    ];
  }

  // Count code points to match the backend's character count.
  const contentLength = $derived([...content].length);
  const overLimit = $derived(contentLength > LIMITS.content);

  /** @returns {Record<string, string>} */
  function validate() {
    /** @type {Record<string, string>} */
    const e = {};
    const t = title.trim();
    if (!t) e.title = 'Title is required.';
    else if ([...t].length > LIMITS.title) e.title = `Title must be at most ${LIMITS.title} characters.`;
    if ([...description].length > LIMITS.description)
      e.description = `Description must be at most ${LIMITS.description} characters.`;
    if (parseTags(tagsText).length > LIMITS.tags) e.tags = `Use at most ${LIMITS.tags} tags.`;
    if (content.length === 0) e.content = 'Content is required.';
    else if (contentLength > LIMITS.content)
      e.content = `Content must be at most ${LIMITS.content.toLocaleString('en-US')} characters.`;
    return e;
  }

  // Persistent live region text: announced when validation errors appear.
  const errorSummary = $derived.by(() => {
    const names = Object.keys(errors);
    if (!names.length) return '';
    return `The form has ${names.length} ${names.length === 1 ? 'error' : 'errors'}. Check: ${names.join(', ')}.`;
  });

  /** @type {HTMLButtonElement | undefined} */
  let previewButton = $state();

  async function togglePreview() {
    showPreview = !showPreview;
    await tick();
    if (!showPreview) document.getElementById('tsf-content')?.focus();
    else previewButton?.focus();
  }

  function isBlank() {
    return !title && !description && !tagsText && !content;
  }

  // Debounced draft autosave.
  $effect(() => {
    const snapshot = { title, description, tags: tagsText, contentType, content };
    const blank = isBlank();
    const timer = setTimeout(() => {
      try {
        if (blank) localStorage.removeItem(draftKey);
        else localStorage.setItem(draftKey, JSON.stringify(snapshot));
      } catch {
        // storage full/unavailable: autosave is best-effort
      }
    }, DRAFT_DEBOUNCE_MS);
    return () => clearTimeout(timer);
  });

  function clearDraft() {
    try {
      localStorage.removeItem(draftKey);
    } catch {
      // ignore
    }
  }

  function discardDraft() {
    clearDraft();
    title = str(initial?.title);
    description = str(initial?.description);
    tagsText = (initial?.tags ?? []).join(', ');
    contentType = initial?.contentType ?? 'other';
    content = str(initial?.content);
    restored = false;
  }

  /** @param {SubmitEvent} ev */
  async function submit(ev) {
    ev.preventDefault();
    if (submitting) return;
    formError = '';
    errors = validate();
    if (Object.keys(errors).length) {
      const first = Object.keys(errors)[0];
      document.getElementById(`tsf-${first}`)?.focus();
      return;
    }
    const input = {
      title: title.trim(),
      content,
      description: description.trim() || undefined,
      tags: parseTags(tagsText),
      contentType,
    };
    submitting = true;
    try {
      const saved = editing
        ? await updateTextSource(projectId, initial.id, input)
        : await createTextSource(projectId, input);
      clearDraft();
      restored = false;
      onsaved?.(saved);
    } catch (err) {
      if (err instanceof TextSourceValidationError) {
        errors = err.fieldErrors;
        formError = err.message;
        const first = Object.keys(err.fieldErrors)[0];
        document.getElementById(`tsf-${first}`)?.focus();
      } else {
        formError = /** @type {Error} */ (err).message || 'Something went wrong.';
      }
    } finally {
      submitting = false;
    }
  }
</script>

<form class="tsf" class:modal onsubmit={submit} novalidate aria-label={editing ? 'Edit text source' : 'New text source'}>
  {#if restored}
    <p class="tsf-notice" role="status">
      Draft restored.
      <button type="button" onclick={discardDraft}>Discard draft</button>
    </p>
  {/if}

  <div class="tsf-errors" aria-live="polite" aria-atomic="true" role="status">
    {#if formError}<p class="tsf-error">{formError}</p>{/if}
    <span class="sr-only">{errorSummary}</span>
  </div>

  <div class="tsf-grid">
    <div class="tsf-meta">
      <label for="tsf-title">Title</label>
      <input
        id="tsf-title"
        required
        aria-required="true"
        bind:value={title}
        maxlength={LIMITS.title}
        aria-invalid={errors.title ? 'true' : undefined}
        aria-describedby={errors.title ? 'tsf-title-err' : undefined}
      />
      {#if errors.title}<p id="tsf-title-err" class="tsf-error" >{errors.title}</p>{/if}

    </div>

    <div class="tsf-body">
      <div class="tsf-body-head">
        <label for="tsf-content">Content</label>
        <button type="button" bind:this={previewButton} aria-pressed={showPreview} onclick={togglePreview}>
          {modal ? 'Preview' : showPreview ? 'Edit' : 'Preview'}
          {#if modal}<span class="preview-switch" aria-hidden="true"></span>{/if}
        </button>
      </div>
      {#if showPreview}
        <pre class="tsf-preview" aria-label="Preview" tabindex="0">{content}</pre>
      {:else}
        <textarea
          id="tsf-content"
          rows="7"
          required
          aria-required="true"
          bind:value={content}
          aria-invalid={errors.content || overLimit ? 'true' : undefined}
          aria-describedby="tsf-counter{errors.content ? ' tsf-content-err' : ''}"
        ></textarea>
      {/if}
      <p id="tsf-counter" class="tsf-counter" class:over={overLimit}>
        {contentLength.toLocaleString('en-US')} / {LIMITS.content.toLocaleString('en-US')}
      </p>
      {#if errors.content}<p id="tsf-content-err" class="tsf-error" >{errors.content}</p>{/if}
    </div>
    <div class="tsf-meta">
      <label for="tsf-contentType">Type</label>
      <select id="tsf-contentType" bind:value={contentType} aria-invalid={errors.contentType ? 'true' : undefined} aria-describedby={errors.contentType ? 'tsf-contentType-err' : undefined}>
        {#each CONTENT_TYPES as t (t)}<option value={t}>{t}</option>{/each}
      </select>
      {#if errors.contentType}<p id="tsf-contentType-err" class="tsf-error">{errors.contentType}</p>{/if}

      <label for="tsf-description">Description (optional)</label>
      <textarea
        id="tsf-description"
        rows="3"
        bind:value={description}
        aria-invalid={errors.description ? 'true' : undefined}
        aria-describedby={errors.description ? 'tsf-description-err' : undefined}
      ></textarea>
      {#if errors.description}
        <p id="tsf-description-err" class="tsf-error" >{errors.description}</p>
      {/if}

      <label for="tsf-tags">Tags (comma separated, max {LIMITS.tags})</label>
      <input
        id="tsf-tags"
        bind:value={tagsText}
        aria-invalid={errors.tags ? 'true' : undefined}
        aria-describedby={errors.tags ? 'tsf-tags-err' : undefined}
      />
      {#if errors.tags}<p id="tsf-tags-err" class="tsf-error" >{errors.tags}</p>{/if}
    </div>
  </div>

  <div class="tsf-actions">
    {#if modal && oncancel}<button type="button" onclick={oncancel}>Cancel</button>{/if}
    <button type="submit" disabled={submitting}>
      {submitting ? 'Saving…' : editing ? 'Save changes' : 'Create'}
    </button>
    {#if !modal && oncancel}<button type="button" onclick={() => oncancel?.()}>Cancel</button>{/if}
  </div>
</form>

<style>
  .sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
  .tsf { color:#203a2b; font-size:13px; }
  .tsf-grid, .tsf-meta, .tsf-body { display:grid; gap:6px; min-width:0; }
  .tsf-grid { gap:16px; }
  label { font-weight:600; }
  .tsf-meta label:not(:first-child) { margin-top:8px; }
  input, select, textarea, .tsf-preview {
    width:100%; box-sizing:border-box; padding:9px 11px; border:1px solid #bdcdc2;
    border-radius:8px; background:white; color:#23362b; font:inherit; line-height:1.5;
  }
  textarea { resize:vertical; }
  :is(input, select, textarea, button, pre):focus-visible { outline:2px solid #477359; outline-offset:2px; }
  [aria-invalid=true] { border-color:#ac3842; }
  .tsf-body-head, .tsf-actions { display:flex; align-items:center; justify-content:space-between; gap:8px; }
  .tsf-preview { white-space:pre-wrap; overflow-wrap:anywhere; min-height:10rem; margin:0; background:#f2f6f3; }
  .tsf-counter { margin:0; text-align:right; color:#536459; font-size:11px; font-variant-numeric:tabular-nums; }
  .tsf-counter.over, .tsf-error { color:#a3313b; }
  button { cursor:pointer; min-height:36px; border:1px solid #c7d5cb; border-radius:8px; padding:6px 12px; background:white; color:#30513d; font:600 12px var(--sans); }
  button:hover:not(:disabled) { background:#edf4ef; }
  .tsf-actions { justify-content:flex-start; flex-wrap:wrap; margin-top:18px; padding-top:14px; border-top:1px solid #dce6df; }
  .tsf-actions button { min-height:44px; }
  .tsf-actions button[type=submit] { flex:1; background:#305440; border-color:#305440; color:white; }
  .tsf-actions button[type=submit]:hover:not(:disabled) { background:#234331; }
  button:disabled { opacity:.65; cursor:default; }
  @media (prefers-reduced-motion:no-preference) {
    button { transition:background-color 150ms ease, transform 120ms ease; }
    button:active:not(:disabled) { transform:translateY(1px); }
  }
  .modal .tsf-actions { justify-content:flex-end; }
  .modal .tsf-actions button[type=submit] { flex:initial; }
  .modal .tsf-body-head button { display:inline-flex; align-items:center; gap:6px; border:0; background:transparent; padding:0 4px; }
  .preview-switch { display:inline-flex; align-items:center; width:28px; height:16px; border-radius:10px; background:#87978b; }
  .preview-switch::before { content:''; width:12px; height:12px; margin-left:2px; background:white; border-radius:50%; }
  [aria-pressed=true] .preview-switch { background:#305440; }
  [aria-pressed=true] .preview-switch::before { transform:translateX(12px); }
  @media(min-width:620px) {
    .modal .tsf-grid { grid-template-columns:repeat(2,minmax(0,1fr)); grid-template-rows:auto 1fr; gap:12px 20px; }
    .modal .tsf-meta { grid-column:1; align-self:start; }
    .modal .tsf-body { grid-column:2; grid-row:1 / span 2; grid-template-rows:auto 1fr auto; }
    .modal .tsf-body textarea { min-height:200px; max-height:max(200px, 52dvh); overflow-y:auto; }
  }
</style>
