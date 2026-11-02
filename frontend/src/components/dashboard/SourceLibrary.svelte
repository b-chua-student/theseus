<script>
  let { icon } = $props();
  // TODO(API): Connect project sources and upload only after backend contracts exist.
</script>

      <aside class="source-card surface" aria-labelledby="sources-heading">
        <h2 id="sources-heading">{@render icon('books')} Project Source Library</h2>
        <div class="source-empty"><span class="source-icon">{@render icon('books', 24)}</span><h3>Your research sources</h3><p>Source uploads and reference management are not available yet.</p></div>
        <button type="button" class="source-upload" disabled title="Source upload is not connected">+ Upload Source</button>
      </aside>
<style>
.source-card, .source-card * { box-sizing:border-box; }
  button { font: inherit; color: inherit; cursor: pointer; } button:disabled { cursor: default; opacity: 1; } button:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }
.surface { background: var(--surface); border: 1.5px solid transparent; border-radius: 14px; box-shadow: var(--shadow); }
.source-upload { display: inline-flex; align-items: center; justify-content: center; gap: 6px; font-size: 10.5px; font-weight: 600; border-radius: 7px; padding: 8px 14px; border: 1px solid var(--border); background: #f4f5f3; white-space: nowrap; }
.source-card { padding: 20px; }
.source-card h2 { margin-bottom: 14px; }
.source-empty { border: 1px solid #e2e6e2; border-radius: 9px; background: var(--surface-muted); padding: 20px 12px; text-align: center; }
.source-empty p { margin: 0; color: #78867f; font-size: 10px; line-height: 1.6; }
.source-upload { margin-top: 12px; width: 100%; color: #78867f; }
h2 { display: flex; align-items: center; gap: 7px; font-size: 10.5px; text-transform: uppercase; letter-spacing: .04em; font-weight: 700; margin: 0; }
h3 { margin: 0 0 6px; font-size: 11px; }
.source-icon { display:inline-flex; color:var(--accent-border); margin-bottom:8px; }
@media(max-width:767px) { .source-card { margin-top:4px; } }
</style>
