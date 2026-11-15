<script>
  import { untrack, tick } from 'svelte';
  import { listTextSources, searchTextSources, deleteTextSource } from '../../lib/api/textSources.js';
  import TextSourceCard from './TextSourceCard.svelte';
  import ConfirmDelete from './ConfirmDelete.svelte';

  /**
   * @type {{
   *   projectId: string,
   *   onedit: (source: import('../../lib/api/textSources.js').TextSourceSummary) => void,
   *   oncreate?: () => void,
   *   onchange?: () => void,
   *   refreshKey?: number,
   *   pageSize?: number,
   *   debounceMs?: number,
   * }}
   */
  let { projectId, onedit, oncreate, onchange, refreshKey = 0, pageSize = 20, debounceMs = 300 } = $props();

  // ── filter state ──────────────────────────────────────────────────────────
  let queryInput = $state('');
  let tagInput = $state('');
  let query = $state('');
  let tag = $state('');
  let contentType = $state('');
  let sort = $state('updatedAt');
  let page = $state(1);

  // ── data state ────────────────────────────────────────────────────────────
  /** @type {import('../../lib/api/textSources.js').TextSourceSummary[]} */
  let items = $state([]);
  let total = $state(0);
  let loading = $state(false);
  let error = $state('');
  let loadFailed = $state(false);

  // ── delete state ──────────────────────────────────────────────────────────
  /** @type {import('../../lib/api/textSources.js').TextSourceSummary | null} */
  let pendingDelete = $state(null);
  let deleteBusy = $state(false);
  let deleteError = $state('');

  const searching = $derived(query !== '');
  const filtered = $derived(searching || tag !== '' || contentType !== '');
  const totalPages = $derived(Math.max(1, Math.ceil(total / pageSize)));

  // Debounce the free-text inputs; any change restarts from page 1.
  $effect(() => {
    const q = queryInput.trim();
    const t = tagInput.trim();
    const handle = setTimeout(() => {
      if (q !== untrack(() => query) || t !== untrack(() => tag)) {
        query = q;
        tag = t;
        page = 1;
      }
    }, debounceMs);
    return () => clearTimeout(handle);
  });

  let requestId = 0;

  async function load() {
    const req = ++requestId;
    loading = true;
    error = '';
    loadFailed = false;
    try {
      const common = { contentType: contentType || undefined, tag: tag || undefined, page, pageSize };
      const result = query
        ? await searchTextSources(projectId, { q: query, ...common })
        : await listTextSources(projectId, { sort, ...common });
      if (req !== requestId) return;
      items = result.items;
      total = result.total;
    } catch (e) {
      if (req !== requestId) return;
      error = e.message;
      loadFailed = true;
    } finally {
      if (req === requestId) loading = false;
    }
  }

  // Reload whenever a query input or refreshKey changes.
  $effect(() => {
    query; tag; contentType; sort; page; refreshKey;
    untrack(load);
  });

  function setFilter(apply) {
    apply();
    page = 1;
  }

  // ── delete ────────────────────────────────────────────────────────────────
  /** @type {HTMLElement | null} */
  let opener = null;
  let headingEl = $state();

  async function closeDelete() {
    pendingDelete = null;
    await tick();
    // Return focus to the trigger if it still exists, else to the section heading.
    if (opener && opener.isConnected) opener.focus();
    else headingEl?.focus();
    opener = null;
  }

  function askDelete(source) {
    opener = /** @type {HTMLElement | null} */ (document.activeElement);
    pendingDelete = source;
    deleteError = '';
  }

  async function confirmDelete() {
    if (!pendingDelete) return;
    deleteBusy = true;
    deleteError = '';
    try {
      await deleteTextSource(projectId, pendingDelete.id);
      // Deleting the last item on a page would leave it empty; step back.
      if (items.length === 1 && page > 1) page -= 1;
      else await load();
      await closeDelete();
      onchange?.();
    } catch (e) {
      deleteError = e.message;
    } finally {
      deleteBusy = false;
    }
  }
</script>

<section class="text-sources" aria-labelledby="text-sources-heading">
  <div class="header">
    <h3 id="text-sources-heading" tabindex="-1" bind:this={headingEl}>Text sources{total ? ` (${total})` : ''}</h3>
    {#if oncreate}<button type="button" class="add" onclick={oncreate}>+ Add text</button>{/if}
  </div>

  <form class="controls" role="search" onsubmit={(e) => e.preventDefault()}>
    <label class="wide">
      <span class="sr-only">Search text sources</span>
      <input type="search" placeholder="Search text sources" bind:value={queryInput} />
    </label>
    <label>
      <span class="sr-only">Filter by type</span>
      <select value={contentType} onchange={(e) => setFilter(() => (contentType = e.currentTarget.value))}>
        <option value="">All types</option>
        <option value="documentation">Documentation</option>
        <option value="notes">Notes</option>
        <option value="code">Code</option>
        <option value="other">Other</option>
      </select>
    </label>
    <label>
      <span class="sr-only">Filter by tag</span>
      <input type="text" placeholder="Tag" bind:value={tagInput} />
    </label>
    <label>
      <span class="sr-only">Sort by</span>
      <select
        value={sort}
        disabled={searching}
        title={searching ? 'Search results are ordered by relevance' : undefined}
        onchange={(e) => setFilter(() => (sort = e.currentTarget.value))}
      >
        <option value="updatedAt">Recently updated</option>
        <option value="title">Title</option>
      </select>
    </label>
  </form>

  {#if pendingDelete}
    <ConfirmDelete
      title={pendingDelete.title}
      busy={deleteBusy}
      error={deleteError}
      onconfirm={confirmDelete}
      oncancel={closeDelete}
    />
  {/if}

  {#if error}
    <div class="error-banner" role="alert">
      {error} {#if loadFailed}<button type="button" onclick={load}>Retry</button>{/if}
    </div>
  {/if}

  <div aria-live="polite">
    {#if loading && items.length === 0}
      <p class="status" role="status">Loading text sources…</p>
    {:else if loadFailed}
      <!-- error banner explains the failure -->
    {:else if items.length === 0}
      <div class="empty">
        {#if filtered}
          <h4>No matching text sources</h4>
          <p>Try a different search or clear the filters.</p>
        {:else}
          <h4>No text sources yet</h4>
          <p>Paste notes, documentation or code to ground the assistant.</p>
          {#if oncreate}<button type="button" class="add" onclick={oncreate}>+ Add text</button>{/if}
        {/if}
      </div>
    {:else}
      <ul class="cards" aria-busy={loading}>
        {#each items as source (source.id)}
          <li><TextSourceCard {source} {onedit} ondelete={askDelete} /></li>
        {/each}
      </ul>
    {/if}
  </div>

  {#if total > pageSize}
    <nav class="pager" aria-label="Text sources pages">
      <button type="button" disabled={page <= 1 || loading} onclick={() => (page -= 1)}>Previous</button>
      <span>Page {page} of {totalPages}</span>
      <button type="button" disabled={page >= totalPages || loading} onclick={() => (page += 1)}>Next</button>
    </nav>
  {/if}
</section>

<style>
  .text-sources { margin-top: 16px; display: grid; gap: 10px; }
  .header { display: flex; justify-content: space-between; align-items: center; }
  h3 { margin: 0; font-size: 10.5px; text-transform: uppercase; letter-spacing: .04em; }
  h4 { margin: 0 0 4px; font-size: 11px; }
  .controls { display: flex; flex-wrap: wrap; gap: 6px; }
  .controls label { flex: 1 1 90px; min-width: 0; }
  .controls .wide { flex-basis: 100%; }
  input, select { width: 100%; font: inherit; font-size: 10.5px; padding: 6px 8px; border: 1px solid #aeb9b3; border-radius: 6px; background: white; color: var(--text); }
  input:focus-visible, select:focus-visible, button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  .sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
  .cards { list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; }
  .empty { border: 1px solid #e2e6e2; border-radius: 9px; background: var(--surface-muted); padding: 16px 12px; text-align: center; }
  .empty p { margin: 0 0 10px; font-size: 10px; color: #78867f; }
  .status { text-align: center; font-size: 10.5px; color: var(--text-muted); }
  .error-banner { background: #fdf0f0; border: 1px solid #e8b4b4; border-radius: 8px; color: #b94040; font-size: 10.5px; padding: 8px 12px; display: flex; gap: 10px; align-items: center; }
  .pager { display: flex; justify-content: space-between; align-items: center; font-size: 10px; }
  button { font: inherit; font-size: 10px; border: 1px solid var(--border); border-radius: 6px; padding: 5px 10px; background: #f4f5f3; color: inherit; cursor: pointer; }
  button:disabled { opacity: .5; cursor: default; }
  button.add { font-weight: 600; }
  button, input, select { min-height: 32px; }
  @media (max-width: 767px) {
    button, input, select { min-height: 44px; }
    input, select { font-size: 16px; }
    .controls label { flex-basis: 100%; }
    .pager { gap: 8px; }
  }
  @media (min-width: 768px) {
    .cards { grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); }
  }
</style>
