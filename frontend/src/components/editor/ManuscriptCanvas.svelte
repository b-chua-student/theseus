<script>
  // The parent creates and destroys Tiptap using this bound mount element.
  let { zoom = 100, pageCount = 1, status = 'ready', error = '', onretry, element = $bindable() } = $props();
</script>

    <main class="document-canvas" aria-label="Manuscript editor">
      <div class="document-sheet" style:zoom={zoom / 100}>
        <div class="paper-rule"></div>
        <!-- Tiptap remains the sole editable document and owns all saved content. -->
        <div class="editor-mount" bind:this={element}></div>
        {#if status === 'loading'}
          <div class="canvas-overlay" role="status"><span class="spinner" aria-hidden="true"></span>Loading manuscript…</div>
        {:else if status === 'error'}
          <div class="canvas-overlay" role="alert">
            <strong>Couldn't load this manuscript</strong>
            <span>{error}</span>
            <button type="button" onclick={() => onretry?.()}>Try again</button>
          </div>
        {/if}
        <footer class="paper-footer"><span>{pageCount} manual page(s)</span><span>Manual page breaks</span></footer>
      </div>
    </main>
<style>
  .editor-mount :global(.tiptap:not(.ProseMirror-focused) .toolbar-selection) { background: #bed1cb; }
  .editor-mount :global(.tiptap span[style*="font-size"]) { line-height: 1.3; }

  .document-canvas, .document-canvas *, .editor-mount :global(.tiptap *) { box-sizing: border-box; }
  .document-canvas { flex: 1; min-width: 0; overflow: auto; padding: 28px 24px; background: var(--canvas); }
  .document-sheet { width: 100%; max-width: 540px; min-height: 700px; padding: 40px 44px; margin: 0 auto; display: flex; flex-direction: column; background: var(--paper); border: 1.5px solid var(--accent); box-shadow: 0 8px 26px -4px rgb(28 42 36 / 14%), 0 2px 6px -1px rgb(28 42 36 / 6%); }
  .document-sheet { position: relative; }
  .canvas-overlay { position: absolute; inset: 0; z-index: 5; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; padding: 24px; text-align: center; background: color-mix(in srgb, var(--paper) 92%, transparent); font: 12px var(--sans); color: var(--text-muted); }
  .canvas-overlay strong { color: var(--text-h); font-size: 13px; }
  .canvas-overlay button { margin-top: 4px; padding: 6px 14px; border: 1px solid var(--accent); border-radius: 6px; background: var(--accent); color: white; font: 600 11px var(--sans); cursor: pointer; }
  .spinner { width: 18px; height: 18px; border: 2px solid #cbd6cd; border-top-color: var(--accent); border-radius: 50%; animation: spin .8s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  @media (prefers-reduced-motion: reduce) { .spinner { animation-duration: 3s; } }
  .paper-rule { border-top: 1px solid #e2e6e2; margin-bottom: 24px; }
  .editor-mount { flex: 1; min-width: 0; }
  .editor-mount :global(.tiptap) { outline: none; min-height: 520px; padding: 0; border: 0; font-family: var(--document-font); font-size: 16px; line-height: 1.68; color: #2a342f; overflow-wrap: anywhere; }
  .editor-mount :global(.tiptap > :first-child) { margin-top: 0; }
  .editor-mount :global(.tiptap p) { margin: 0 0 1em; }
  .editor-mount :global(.tiptap h1) { font-size: 22px; font-weight: 700; line-height: 1.3; padding-bottom: 16px; margin: 24px 0 20px; border-bottom: 1px solid #e2e6e2; color: var(--text-h); }
  .editor-mount :global(.tiptap h2) { font-size: 13.5px; font-weight: 700; margin: 24px 0 10px; color: var(--text-h); }
  .editor-mount :global(.tiptap ul), .editor-mount :global(.tiptap ol) { padding-left: 1.4rem; margin: .4rem 0; }
  .editor-mount :global(.tiptap ul) { list-style: disc; }.editor-mount :global(.tiptap ol) { list-style: decimal; }
  .editor-mount :global(.tiptap pre) { background: #2e2b29; color: white; padding: 12px 16px; border-radius: 8px; overflow-x: auto; white-space: pre; font: 12px/1.6 var(--mono); }
  .editor-mount :global(.tiptap blockquote) { border-left: 3px solid #9cb4a8; padding-left: 16px; margin-left: 0; color: var(--accent-border); }
  .paper-footer { margin-top: 40px; padding-top: 12px; border-top: 1px solid #e2e6e2; display: flex; justify-content: space-between; font: 8.5px var(--mono); color: #5a6760; }.paper-footer span:last-child { font-size: 8px; color: #9aa59f; }

@media (max-width: 1023px) { .document-canvas { max-height: 75dvh; flex: auto; } }

@media (max-width: 560px) { .document-canvas { padding: 20px 12px; } .document-sheet { padding: 28px 22px; } }

  .editor-mount :global(.tiptap [data-manual-page-break]) { display: block; height: 56px; margin: 36px -44px; background: var(--canvas); border-top: 1px solid #aeb9b3; border-bottom: 1px solid #aeb9b3; position: relative; user-select: none; }
  .editor-mount :global(.tiptap [data-manual-page-break]::after) { content: 'MANUAL PAGE BREAK'; position: absolute; inset: 0; display: grid; place-items: center; font: 9px var(--sans); letter-spacing: .08em; color: var(--accent-border); }
  .editor-mount :global(.tiptap [data-manual-page-break].ProseMirror-selectednode) { outline: 2px solid var(--accent); }
  @media (max-width: 560px) { .editor-mount :global(.tiptap [data-manual-page-break]) { margin-left: -22px; margin-right: -22px; } }
</style>
