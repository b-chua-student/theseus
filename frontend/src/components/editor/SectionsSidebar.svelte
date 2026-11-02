<script>
  // The parent owns the document, outline, and section actions.
  let { editor, outline, currentSection, showDialog, sectionOnNextPage, jumpTo, wordCount, icon } = $props();
</script>

    <aside class="sections-panel" aria-label="Sections and pages">
      <div class="sections-body">
        <div class="sections-heading"><h3>Sections &amp; Pages</h3><span class="badge">{outline.length} PAGES</span></div>
        <p class="section-hint">Click a heading or page to jump</p>
        <div class="section-actions"><button type="button" disabled={!editor} onclick={() => showDialog('section')}>+ Section</button><button type="button" disabled={!currentSection} onclick={sectionOnNextPage} title="Insert a page break before the selected section">↵ Next Page</button></div>
        {#each outline as page}
          <button type="button" class="page-label page-jump" onclick={() => jumpTo(page.pos)}>PAGE {page.number}</button>
          {#each page.sections as section}
            <button type="button" class="section-card" class:section-selected={currentSection?.pos === section.pos} onclick={() => jumpTo(section.pos)} title={section.title}>
              <span class="section-icon">{@render icon('document', 13)}</span><span class="section-text"><strong>{section.title}</strong><small>Heading {section.level}</small></span><span class="section-page">p.{page.number}</span>
            </button>
          {:else}<button type="button" class="section-card" onclick={() => jumpTo(page.pos)}><span class="section-text"><strong>Page {page.number}</strong><small>No headings yet</small></span></button>{/each}
        {/each}
      </div>
      <div class="sections-footer"><span>Manuscript</span><span>{wordCount} words</span></div>
    </aside>
<style>
  .sections-panel, .sections-panel * { box-sizing: border-box; }
  button { font: inherit; color: inherit; margin: 0; display: inline-flex; align-items: center; justify-content: center; gap: 6px; cursor: pointer; line-height: 1.3; }
  button:disabled { cursor: default; opacity: 1; -webkit-text-fill-color: currentColor; }
  button:not(:disabled):hover { background: #e9ede9; }
  button:focus-visible { outline: 2px solid var(--green); outline-offset: 2px; }
  .sections-panel { width: 195px; flex-shrink: 0; background: #f4f6f3; border-right: 1px solid var(--border); display: flex; flex-direction: column; justify-content: space-between; }
  .sections-body { padding: 12px; overflow-y: auto; flex: 1; }
  .sections-heading { display: flex; align-items: center; justify-content: space-between; gap: 4px; }
  h3 { font-size: 9px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; margin: 0; }
  .badge { background: #dee5df; color: #2f3b35; padding: 2px 6px; border-radius: 3px; font: 600 8px var(--mono); }
  .section-hint { font-size: 8.5px; color: #78867f; margin: 2px 0 10px; }
  .section-actions { display: flex; gap: 4px; margin-bottom: 10px; }
  .section-actions button { flex: 1; border: 1px solid var(--border); border-radius: 5px; padding: 4px 6px; background: white; font-size: 8.5px; font-weight: 600; white-space: nowrap; }
  .section-actions button:last-child { color: var(--green); }
  .page-label { font: 8px var(--mono); letter-spacing: .05em; color: #78867f; margin: 12px 0 6px; }
  .section-card { width: 100%; padding: 9px 8px; border: 1px solid var(--accent-border); border-radius: 7px; background: #e7eee8; text-align: left; gap: 7px; }
  .section-icon { color: var(--green); display: flex; }.section-text { flex: 1; min-width: 0; }.section-text strong { display: block; font-size: 10px; }.section-text small { display: block; font: 8px var(--mono); color: #78867f; margin-top: 3px; }.section-page { font: 8px var(--mono); color: var(--accent-border); }
  .sections-footer { padding: 10px 12px; border-top: 1px solid var(--border); background: #f8faf8; display: flex; justify-content: space-between; gap: 6px; font: 9px var(--mono); color: #3a4640; }

.section-card { margin-bottom: 6px; border-color: var(--border); background: var(--surface); }
.section-card.section-selected { border-color: var(--accent-border); background: #e7eee8; }
.section-text strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.page-jump { padding: 2px 0; border: 0; background: transparent; }
@media (max-width: 1023px) { .sections-panel { width: 100%; border-right: 0; border-bottom: 1px solid var(--border); } .sections-body { padding: 12px 16px; } .section-actions { max-width: 240px; } .section-card { max-width: 280px; } .sections-footer { display: none; } }
</style>
