<script>
  let { doc, onselect, icon } = $props();
  const formatDate = (ts) => {
    if (ts === null || ts === undefined || ts === '') return 'Not available';
    const date = new Date(Number(ts) * 1000);
    return Number.isNaN(date.getTime()) ? 'Not available' : date.toLocaleString();
  };
  const commitLabel = (value) => typeof value === 'string' && value.length ? value.slice(0, 7) : 'No commit';
</script>

            <button type="button" class="manuscript-card surface" onclick={() => onselect?.(doc.document_id)} aria-label={`Open manuscript ${doc.document_id}`}>
              <span class="card-top"><span class="document-badge">{@render icon('document', 11)} Manuscript</span><span class="modified">{@render icon('clock', 12)} {formatDate(doc.last_modified)}</span></span>
              <span class="document-title">{doc.document_id}</span>
              <span class="author">Author: {doc.author || 'Not specified'}</span>
              <span class="card-footer"><span class="commit">Last commit <code>{commitLabel(doc.last_commit_id)}</code></span><span class="open-label">Open Manuscript Editor <span>›</span></span></span>
            </button>
<style>
.manuscript-card, .manuscript-card * { box-sizing:border-box; }
  button { font: inherit; color: inherit; cursor: pointer; } button:disabled { cursor: default; opacity: 1; } button:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }
.surface { background: var(--surface); border: 1.5px solid transparent; border-radius: 14px; box-shadow: var(--shadow); }
.manuscript-card { display: block; width: 100%; padding: 20px; text-align: left; transition: transform .18s ease,border-color .18s ease,box-shadow .18s ease; }
.manuscript-card:hover { transform: translateY(-2px); border-color: var(--accent); box-shadow: 0 10px 22px -4px rgb(30 45 38 / 16%); }
.card-top { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; }
.document-badge { display: inline-flex; align-items: center; gap: 5px; background: var(--accent); color: white; border-radius: 4px; padding: 3px 8px; font: 500 9px var(--mono); }
.modified { display: inline-flex; align-items: center; gap: 4px; color: var(--text-muted); font-size: 9.5px; }
.document-title { display: block; font-size: 14.5px; font-weight: 700; color: var(--text-h); margin-bottom: 4px; overflow-wrap: anywhere; }
.author { display: block; font: 9.5px/1.5 var(--mono); color: var(--text-muted); margin-bottom: 14px; overflow-wrap: anywhere; }
.card-footer { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; padding-top: 10px; border-top: 1px solid #e6eae6; }
.commit { font: 9.5px var(--mono); color: #5a6760; }
.commit code { font: inherit; color: var(--accent); margin-left: 6px; }
.open-label { display: inline-flex; align-items: center; gap: 5px; font-size: 10px; font-weight: 700; }
.open-label > span { font-size: 15px; }
@media(max-width:420px) { .manuscript-card { padding:16px; } }
@media(prefers-reduced-motion:reduce) { .manuscript-card { transition:none; }.manuscript-card:hover { transform:none; } }
</style>
