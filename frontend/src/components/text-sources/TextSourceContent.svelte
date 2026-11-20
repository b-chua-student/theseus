<script>
  import { getTextSource } from '../../lib/api/textSources.js';

  /** @type {{ projectId: string, sourceId: string }} */
  let { projectId, sourceId } = $props();
  let expanded = $state(false);
  let loading = $state(false);
  let content = $state('');
  let error = $state('');
  let requestId = 0;

  async function load() {
    const request = ++requestId;
    loading = true;
    error = '';
    try {
      const source = await getTextSource(projectId, sourceId);
      if (request === requestId) content = source.content;
    } catch (e) {
      if (request === requestId) error = e.message;
    } finally {
      if (request === requestId) loading = false;
    }
  }

  function toggle() {
    expanded = !expanded;
    if (expanded) load();
    else requestId += 1;
  }
</script>

<div class="viewer">
  <button type="button" aria-expanded={expanded} onclick={toggle}>
    {expanded ? 'Close content' : 'View content'}
  </button>
  {#if expanded}
    {#if loading}
      <p role="status">Loading source content…</p>
    {:else if error}
      <div role="alert">{error} <button type="button" onclick={load}>Retry</button></div>
    {:else}
      <pre role="region" aria-label="Source content">{content}</pre>
    {/if}
  {/if}
</div>

<style>
  .viewer { min-width: 0; }
  button { font: inherit; font-size: 10px; border: 1px solid var(--border); border-radius: 5px; padding: 3px 9px; background: transparent; color: inherit; cursor: pointer; }
  button:hover { background: #eaece9; }
  button:focus-visible, pre:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  p, [role='alert'] { font-size: 11px; }
  [role='alert'] { color: #b94040; margin-top: 8px; }
  pre { white-space: pre-wrap; overflow-wrap: anywhere; max-height: 60vh; overflow: auto; font: 12px/1.6 var(--mono, monospace); padding: 12px; border: 1px solid var(--border); border-radius: 6px; background: var(--surface, white); user-select: text; }
  @media (max-width: 767px) { button { min-height: 44px; } }
</style>
