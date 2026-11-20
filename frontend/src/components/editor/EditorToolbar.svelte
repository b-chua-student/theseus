<script>
  // Presentation and local controls. The parent owns the shared Tiptap editor.
  let { editor, fonts, sizes, fontFamily, fontSize, setFont, tools, active, runMenu, showDialog, isAligned, align, outline, currentPage, jumpTo, addPage, zoom, changeZoom, wordCount, icon } = $props();
  let sizeDraft = $state('16');
  let editingSize = $state(false);
  let sizeSelection;
  $effect(() => { if (!editingSize) sizeDraft = String(parseFloat(fontSize)); });
  function beginSize() {
    editingSize = true;
    if (editor) sizeSelection = { from: editor.state.selection.from, to: editor.state.selection.to };
  }
  function updateSize(value) {
    const number = Number(value);
    if (String(value).trim() && Number.isFinite(number) && number >= 1 && number <= 300) {
      setFont('fontSize', `${number}px`, { focus: false, selection: sizeSelection });
    }
  }
  function finishSize() {
    editingSize = false;
    sizeDraft = String(parseFloat(fontSize));
  }
  function chooseSize(event) {
    updateSize(event.currentTarget.value);
    finishSize();
    event.currentTarget.value = '';
    editor?.commands.focus();
  }
</script>

  <div class="formatting-bar" role="group" aria-label="Manuscript formatting">
    <div class="format-tools">
      <select class="font-select" aria-label="Font family" disabled={!editor} value={fontFamily} onchange={event => setFont('fontFamily', event.currentTarget.value)}>{#each fonts as font (font)}<option value={font}>{font}</option>{/each}</select>
      <div class="size-control">
        <input class="font-size-input" type="number" min="1" max="300" step="any" aria-label="Font size" title="Font size in pixels (1–300)" disabled={!editor} value={sizeDraft} onfocus={beginSize} oninput={event => { sizeDraft = event.currentTarget.value; updateSize(sizeDraft); }} onblur={finishSize} onkeydown={event => { if (event.key === 'Enter') { event.preventDefault(); editor?.commands.focus(); } }} />
        <select class="size-presets" aria-label="Preset font size" title="Preset font sizes" disabled={!editor} onfocus={beginSize} onblur={finishSize} onchange={chooseSize}><option value="">px</option>{#each sizes as size (size)}<option value={parseFloat(size)}>{parseFloat(size)} px</option>{/each}</select>
      </div>
      <span class="divider"></span>
      {#each tools as t (t.label)}
        <button type="button" class="format-button" class:active={t.name && active(t.name, t.attrs)}
          class:bold={t.label === 'Bold'} class:italic={t.label === 'Italic'}
          disabled={!editor} title={t.label} aria-label={t.label}
          aria-pressed={t.name ? !!active(t.name, t.attrs) : undefined}
          onclick={() => t.run(editor.chain().focus()).run()}>
          {#if t.label === 'Bold'}B{:else if t.label === 'Italic'}I
          {:else if t.label === 'Bullets'}{@render icon('bullets', 12)}
          {:else if t.label === 'Numbered'}{@render icon('numbered', 12)}
          {:else if t.label === 'Undo'}↶{:else if t.label === 'Redo'}↷
          {:else if t.label === 'Code'}&lt;/&gt;{:else}{t.label}{/if}
        </button>
        {#if t.label === 'Italic'}
          <button type="button" class="format-button underline" class:active={active('underline')} disabled={!editor} onclick={() => runMenu('underline')} title="Underline" aria-label="Underline" aria-pressed={!!active('underline')}>U</button>
        {/if}
      {/each}
      <button type="button" class="format-button citation" disabled={!editor} onclick={() => showDialog('citation')} title="Insert citation text" aria-label="Insert citation">99</button>
      <span class="divider"></span>
      {#each ['left', 'center', 'right', 'justify'] as alignment (alignment)}
        <button type="button" class="format-button" class:active={isAligned(alignment)} disabled={!editor} onclick={() => align(alignment)} title={`${alignment} alignment`} aria-label={`${alignment} alignment`} aria-pressed={isAligned(alignment)}>{@render icon(alignment, 12)}</button>
      {/each}
    </div>
    <div class="page-tools">
      <div class="page-pill"><span>Pages:</span><div class="page-links">{#each outline as page (page.number)}<button type="button" class:page-number={currentPage.number === page.number} onclick={() => jumpTo(page.pos)} aria-label={`Go to page ${page.number}`}>p.{page.number}</button>{/each}</div><button type="button" disabled={!editor} onclick={addPage} title="Append a manual page" aria-label="Add page">+</button></div>
      <div class="page-pill zoom"><button type="button" disabled={zoom <= 50} onclick={() => changeZoom(-10)} aria-label="Zoom out" title="Zoom out">{@render icon('zoom', 11)} −</button><span>{zoom}%</span><button type="button" disabled={zoom >= 150} onclick={() => changeZoom(10)} aria-label="Zoom in" title="Zoom in">{@render icon('zoom', 11)} +</button></div>
      <span class="word-count">{wordCount} words</span>
    </div>
  </div>


<style>
  .size-control { display: inline-flex; align-items: center; gap: 2px; }
  .format-tools .size-presets { width: 45px; padding: 2px; }

  .font-size-input { width: 66px; height: 24px; padding: 2px 5px; border: 1px solid var(--border); border-radius: 5px; background: white; color: inherit; font: 10.5px var(--sans); }
  .font-size-input:focus-visible { outline: 2px solid var(--green); outline-offset: 2px; }
  button, select { font: inherit; color: inherit; margin: 0; }
  button { display: inline-flex; align-items: center; justify-content: center; gap: 6px; cursor: pointer; line-height: 1.3; }
  button:disabled, select:disabled { cursor: default; opacity: 1; -webkit-text-fill-color: currentColor; }
  button:not(:disabled):hover { background: #e9ede9; }
  button:focus-visible, select:focus-visible { outline: 2px solid var(--green); outline-offset: 2px; }
  .formatting-bar, .formatting-bar * { box-sizing: border-box; }
  .formatting-bar { background: var(--surface-muted); border-bottom: 1px solid var(--border); padding: 6px 16px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; }
  .format-tools, .page-tools { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
  .format-tools select { background: white; border: 1px solid var(--border); border-radius: 5px; padding: 2px 5px; font-size: 10.5px; height: 24px; }
  .font-select { font-family: 'Times New Roman', Times, serif; width: 130px; }
  .divider { height: 14px; width: 1px; background: var(--border); margin: 0 2px; }
  .format-button { width: 24px; height: 24px; padding: 0; background: white; border: 1px solid #e2e6e2; border-radius: 4px; font-size: 10.5px; flex-shrink: 0; }
  .bold, .italic, .underline, .citation { font-family: 'Times New Roman', Times, serif; font-size: 12px; }
  .bold, .citation { font-weight: 700; }.italic { font-style: italic; }.underline { text-decoration: underline; }
  .page-tools { gap: 8px; }
  .page-pill { display: flex; align-items: center; gap: 4px; border: 1px solid var(--border); border-radius: 999px; padding: 2px 10px; background: white; font-size: 9.5px; color: var(--text-muted); white-space: nowrap; }
  .page-pill button { border: 0; background: transparent; color: var(--green); border-radius: 4px; padding: 1px 4px; gap: 2px; }
  .page-pill .page-number { background: var(--green); color: white; font-weight: 600; }
  .zoom, .word-count, .page-number { font-family: var(--mono); }
  .word-count { font-size: 9.5px; color: var(--text-muted); white-space: nowrap; }
  .page-links { display: flex; max-width: 150px; overflow-x: auto; gap: 3px; }
  .formatting-bar { flex-shrink: 0; }
  @media (max-width: 560px) { .formatting-bar { padding: 8px 12px; } }
  .format-button.active { background: var(--green); color: white; border-color: var(--green); }
  .active:not(:disabled):hover { background: var(--accent-hover); }
</style>
