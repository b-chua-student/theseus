<script>
  import { listSources } from '../../lib/api/sources.js';
  import { listIndexedSourceIds } from '../../lib/api/chat.js';
  import {
    allIndexedChecked, clearSelection, setAllIndexed, setManuscript, setSource, setWeb, summarize,
  } from './contextSelection.js';

  // One dropdown for Web, Manuscript and the project's indexed sources. Every change applies
  // at once; there is no Apply step.
  let { projectId, selection = $bindable(), manuscriptAvailable = true } = $props();

  let open = $state(false);
  /** @type {{ id: string, title: string }[]} */
  let sources = $state([]);
  let loading = $state(false);
  let error = $state('');
  let filter = $state('');
  let root = $state();
  let button = $state();
  let request = 0;

  const indexedIds = $derived(sources.map((source) => source.id));
  const visible = $derived.by(() => {
    const needle = filter.trim().toLowerCase();
    return sources.filter((source) => source.title.toLowerCase().includes(needle));
  });
  const summary = $derived(summarize(selection));
  const allChecked = $derived(allIndexedChecked(selection, indexedIds));

  let loadedProject = $state(null);
  $effect(() => {
    if (projectId !== loadedProject) {
      loadedProject = projectId;
      request += 1;
      sources = [];
      open = false;
    }
  });

  async function loadSources() {
    const current = ++request;
    loading = true;
    error = '';
    try {
      // Only indexed sources can supply evidence, so the list is the indexed ones.
      const [all, indexed] = await Promise.all([listSources(projectId), listIndexedSourceIds(projectId)]);
      if (current !== request) return;
      const ready = new Set(indexed);
      sources = all.filter((source) => ready.has(source.id)).map(({ id, title }) => ({ id, title }));
    } catch (e) {
      if (current === request) error = e.message || 'Could not load sources.';
    } finally {
      if (current === request) loading = false;
    }
  }

  function toggle() {
    open = !open;
    if (open) {
      filter = '';
      loadSources();
    }
  }

  function close({ refocus = true } = {}) {
    open = false;
    if (refocus) button?.focus();
  }

  function onkeydown(event) {
    if (!open) return;
    if (event.key === 'Escape') {
      event.stopPropagation();
      close();
      return;
    }
    if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') return;
    const items = [...root.querySelectorAll('.context-menu input:not(:disabled), .context-menu button:not(:disabled)')];
    if (items.length === 0) return;
    event.preventDefault();
    const index = items.indexOf(document.activeElement);
    const next = event.key === 'ArrowDown' ? index + 1 : index < 0 ? items.length - 1 : index - 1;
    items[(next + items.length) % items.length].focus();
  }

  function onwindowclick(event) {
    if (open && root && !root.contains(event.target)) close({ refocus: false });
  }
</script>

<svelte:window onclick={onwindowclick} />

<div class="context-dropdown" bind:this={root} role="presentation" {onkeydown}>
  <button type="button" class="context-button" bind:this={button} aria-expanded={open} aria-haspopup="dialog" onclick={toggle}>
    <span class="context-caption">Context:</span>
    <span class="context-summary">{summary}</span>
  </button>
  {#if open}
    <div class="context-menu" role="dialog" aria-label="Context options">
      <div class="context-fixed">
        <label><input type="checkbox" checked={selection.web} onchange={(event) => selection = setWeb(selection, event.currentTarget.checked)} />Web</label>
        <label><input type="checkbox" checked={selection.manuscript} disabled={!manuscriptAvailable} onchange={(event) => selection = setManuscript(selection, event.currentTarget.checked)} />Manuscript</label>
        <label><input type="checkbox" checked={allChecked} disabled={indexedIds.length === 0} onchange={(event) => selection = setAllIndexed(selection, indexedIds, event.currentTarget.checked)} />All indexed sources</label>
        <button type="button" class="context-clear" onclick={() => selection = clearSelection()}>Clear selection</button>
        <input type="search" aria-label="Filter sources by title" placeholder="Filter sources" bind:value={filter} />
      </div>
      <div class="context-sources" role="group" aria-label="Sources">
        {#if loading && sources.length === 0}<p role="status">Loading sources…</p>
        {:else if error}<p role="alert">{error}</p><button type="button" onclick={loadSources}>Retry</button>
        {:else}
          {#each visible as source (source.id)}
            <label><input type="checkbox" checked={selection.sourceIds.includes(source.id)} onchange={(event) => selection = setSource(selection, source.id, event.currentTarget.checked)} />{source.title}</label>
          {:else}
            <p>{sources.length === 0 ? 'No indexed sources in this project.' : 'No sources match the filter.'}</p>
          {/each}
        {/if}
      </div>
      <p class="context-note">Only indexed content can be used in replies.</p>
    </div>
  {/if}
</div>

<style>
  .context-dropdown { position: relative; margin: 0 0 8px; font-size: 11px; }
  .context-button {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    min-height: 34px;
    padding: 6px 12px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--paper);
    color: var(--accent);
    text-align: left;
    cursor: pointer;
  }
  .context-caption { color: var(--text-muted); font: 10px var(--mono); }
  .context-summary { flex: 1; min-width: 0; overflow-wrap: anywhere; font: 600 11px var(--sans); }
  .context-button::after {
    content: '';
    width: 6px;
    height: 6px;
    flex: none;
    border: solid currentColor;
    border-width: 0 1.5px 1.5px 0;
    transform: translateY(-2px) rotate(45deg);
  }
  .context-button[aria-expanded='true']::after { transform: translateY(2px) rotate(225deg); }
  .context-button:hover, .context-button[aria-expanded='true'] { border-color: var(--accent); }
  .context-dropdown :focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
  .context-menu { position: absolute; z-index: 5; left: 0; right: 0; bottom: calc(100% + 4px); display: flex; flex-direction: column; max-height: min(360px, 50dvh); overflow-y: auto; padding: 8px 10px; border: 1px solid var(--border); border-radius: 8px; background: var(--surface); box-shadow: 0 6px 18px #0002; }
  .context-fixed { display: flex; flex-direction: column; flex-shrink: 0; gap: 2px; padding-bottom: 6px; border-bottom: 1px solid var(--border); }
  .context-menu label { display: flex; align-items: center; gap: 8px; padding: 6px; border-radius: 5px; overflow-wrap: anywhere; }
  .context-menu label:has(input:checked) { background: var(--surface-muted); color: var(--accent); }
  .context-menu label:has(input:disabled) { color: var(--text-muted); }
  .context-menu label:has(input:enabled) { cursor: pointer; }
  .context-menu input[type='checkbox'] { flex: none; margin: 0; accent-color: var(--accent); }
  .context-menu button { align-self: flex-start; padding: 4px 8px; border: 1px solid var(--border); border-radius: 5px; background: var(--surface); }
  .context-fixed input[type='search'] { margin-top: 4px; padding: 5px 7px; border: 1px solid var(--border); border-radius: 5px; background: var(--paper); color: inherit; font: inherit; }
  .context-sources { flex: 1; min-height: 0; overflow-y: auto; padding-top: 4px; }
  .context-menu p { margin: 4px 0; color: var(--text-muted); line-height: 1.5; }
  .context-note { flex-shrink: 0; padding-top: 4px; border-top: 1px solid var(--border); }
</style>
