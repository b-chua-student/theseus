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

  /** @type {{projectId: string, source?: any, onsaved?: (s: any) => void, oncancel?: () => void}} */
  let { projectId, source = null, onsaved, oncancel } = $props();

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
    const seen = new Set();
    for (const t of text.split(',')) {
      const v = t.trim();
      if (v) seen.add(v);
    }
    return [...seen];
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

<form class="tsf" onsubmit={submit} novalidate aria-label={editing ? 'Edit text source' : 'New text source'}>
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

    <div class="tsf-body">
      <div class="tsf-body-head">
        <label for="tsf-content">Content</label>
        <button type="button" bind:this={previewButton} aria-pressed={showPreview} onclick={togglePreview}>
          {showPreview ? 'Edit' : 'Preview'}
        </button>
      </div>
      {#if showPreview}
        <pre class="tsf-preview" aria-label="Preview" tabindex="0">{content}</pre>
      {:else}
        <textarea
          id="tsf-content"
          rows="16"
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
  </div>

  <div class="tsf-actions">
    <button type="submit" disabled={submitting}>
      {submitting ? 'Saving…' : editing ? 'Save changes' : 'Create'}
    </button>
    {#if oncancel}<button type="button" onclick={() => oncancel?.()}>Cancel</button>{/if}
  </div>
</form>

<style>
  .sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
  .tsf { max-width: 100%; }
  input, select, textarea { width: 100%; box-sizing: border-box; font: inherit; }
  button { min-height: 44px; min-width: 44px; }
  .tsf-actions { flex-wrap: wrap; }
  :is(input, select, textarea, button):focus-visible { outline: 2px solid var(--accent, #1a56db); outline-offset: 2px; }
  .tsf-grid {
    display: grid;
    gap: 1rem;
    grid-template-columns: 1fr;
  }
  @media (min-width: 768px) {
    .tsf-grid {
      grid-template-columns: minmax(0, 1fr) minmax(0, 2fr);
    }
  }
  .tsf-meta,
  .tsf-body {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
  .tsf-body-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .tsf-preview {
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    min-height: 16rem;
    margin: 0;
    padding: 0.5rem;
    border: 1px solid currentColor;
  }
  .tsf-counter {
    margin: 0;
    text-align: right;
  }
  .tsf-counter.over,
  .tsf-error {
    color: #b00020;
  }
  .tsf-actions {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
  }
</style>
