<script>
  import TextSourceContent from './TextSourceContent.svelte';
  /**
   * @type {{
   *   projectId?: string,
   *   source: import('../../lib/api/textSources.js').TextSourceSummary,
   *   onedit: (source: import('../../lib/api/textSources.js').TextSourceSummary) => void,
   *   ondelete: (source: import('../../lib/api/textSources.js').TextSourceSummary) => void,
   * }}
   */
  let { source, onedit, ondelete, projectId = '' } = $props();

  const TYPE_LABELS = { documentation: 'Documentation', notes: 'Notes', code: 'Code', other: 'Other' };

  const updated = $derived.by(() => {
    const d = new Date(source.updatedAt);
    return Number.isNaN(d.getTime()) ? '' : d.toLocaleDateString();
  });
</script>

<!-- All user content is rendered as text (never {@html}). -->
<article class="card" aria-label={source.title}>
  <div class="top">
    <h3 class="title">{source.title}</h3>
    <span class="badge">{TYPE_LABELS[source.contentType] ?? source.contentType}</span>
  </div>

  {#if source.snippet}<p class="snippet">{source.snippet}</p>{/if}

  {#if source.tags?.length}
    <ul class="tags" aria-label="Tags">
      {#each source.tags as tag (tag)}<li>{tag}</li>{/each}
    </ul>
  {/if}

  {#if projectId}
    {#key `${projectId}:${source.id}`}
      <TextSourceContent {projectId} sourceId={source.id} />
    {/key}
  {/if}

  <div class="bottom">
    <span class="meta">
      {#if updated}Updated <time datetime={source.updatedAt}>{updated}</time> · {/if}v{source.version}
    </span>
    <span class="actions">
      <button type="button" onclick={() => onedit(source)} aria-label="Edit {source.title}">Edit</button>
      <button type="button" class="danger" onclick={() => ondelete(source)} aria-label="Delete {source.title}">Delete</button>
    </span>
  </div>
</article>

<style>
  .card { display: grid; gap: 6px; padding: 10px 12px; border: 1px solid #e2e6e2; border-radius: 8px; background: var(--surface-muted, #f9faf9); min-width: 0; }
  .top { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }
  .title { margin: 0; font-size: 11px; font-weight: 600; overflow-wrap: anywhere; }
  .badge { font: 600 9px var(--mono, monospace); padding: 2px 6px; border-radius: 4px; background: #dee5df; color: #2f3b35; white-space: nowrap; }
  .snippet { margin: 0; font-size: 10px; color: var(--text-muted); overflow-wrap: anywhere; display: -webkit-box; -webkit-line-clamp: 3; line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
  .tags { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 4px; }
  .tags li { font-size: 9px; padding: 1px 6px; border: 1px solid var(--border); border-radius: 10px; }
  .bottom { display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap; }
  .meta { font-size: 9.5px; color: var(--text-muted); }
  .actions { display: flex; gap: 4px; }
  button { font: inherit; font-size: 10px; border: 1px solid var(--border); border-radius: 5px; padding: 3px 9px; background: transparent; color: inherit; cursor: pointer; }
  button:hover { background: #eaece9; }
  button.danger:hover { background: #fdf0f0; border-color: #e8b4b4; color: #b94040; }
  @media (max-width: 767px) { button { min-height: 44px; min-width: 44px; } }
  button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
</style>
