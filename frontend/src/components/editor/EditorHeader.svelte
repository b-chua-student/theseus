<script>
  // Shared state stays in the parent so menus and keyboard shortcuts stay coordinated.
  let { id, editor, onback, menuItems, runMenu, save, icon, menuOpen = $bindable(null), open = $bindable(false) } = $props();
</script>

  <header class="editor-header">
    <div class="document-controls">
      <button type="button" class="back-button" onclick={onback} title="Back to Project Dashboard" aria-label="Back to Project Dashboard">{@render icon('back')}</button>
      <!-- TODO(API): MERGE
           Connect source/target draft IDs, conflict handling, and server confirmation.
           Enable only after a real merge handler is implemented. -->
      <button type="button" class="pill" disabled title="Merge is not implemented">{@render icon('merge', 12)} Merge</button>
      <!-- TODO(API): DRAFTS
           Replace the display-only Draft-1 label with server-provided draft data.
           Add list/create/load handlers before enabling draft creation or switching.
           The existing dropdown open/close behavior is frontend-only. -->
      <div class="dropdown">
        <button type="button" class="pill branch" onclick={() => menuOpen = menuOpen === 'drafts' ? null : 'drafts'} aria-expanded={menuOpen === 'drafts'}>{@render icon('branch', 12)} Draft-1 {@render icon('chevron', 10)}</button>
        {#if menuOpen === 'drafts'}<div class="dropdown-panel draft-panel"><strong>Current manuscript</strong><p>Only the current document is connected.</p><button type="button" onclick={() => menuOpen = null}>Draft-1 ✓</button><button type="button" disabled>Create draft — unavailable</button></div>{/if}
      </div>
      <div class="document-meta">
        <div class="title-row"><h2 class="name" title={String(id)}>{id}</h2><span class="save-status"><span>•</span> Manual save</span></div>
        <nav class="menu-bar" aria-label="Document menus">
          {#each ['File', 'Edit', 'View', 'Insert', 'Format', 'Tools', 'Help'] as menu}
            <div class="dropdown"><button type="button" onclick={() => menuOpen = menuOpen === menu ? null : menu} aria-expanded={menuOpen === menu}>{menu}</button>
              {#if menuOpen === menu}<div class="dropdown-panel" aria-label={`${menu} actions`}>
                {#each menuItems[menu] as item}<button type="button" disabled={item.disabled || !editor} onclick={() => runMenu(item.action)}>{item.label}{#if item.disabled}<small>Unavailable</small>{/if}</button>{/each}
              </div>{/if}</div>
          {/each}
        </nav>
      </div>
    </div>
    <div class="header-actions">
      <!-- ACTIVE API: Save calls the existing save() function.
           TODO(API): Render chunk/index progress here after a status contract exists. -->
      <button type="button" class="pill primary" onclick={save} disabled={!editor}>{@render icon('save', 12)} Save {@render icon('chevron', 10)}</button>
      <!-- TODO(API): REVISIONS
           Load real revision IDs, timestamps, and content for this document.
           Restoration needs a supported server operation and user confirmation.
           Keep disabled until the history and restore handlers are connected. -->
      <button type="button" class="pill" disabled title="Revision history is not implemented">{@render icon('history', 12)} Revisions</button>
      <button type="button" class="pill" class:active={open} onclick={() => (open = !open)} aria-expanded={open} aria-controls="theseus-chat">{@render icon('panel', 12)} Chat</button>
    </div>
  </header>
<style>
  .editor-header, .editor-header * { box-sizing: border-box; }
  button { font: inherit; color: inherit; margin: 0; }
  button { display: inline-flex; align-items: center; justify-content: center; gap: 6px; cursor: pointer; line-height: 1.3; }
  button:disabled { cursor: default; opacity: 1; -webkit-text-fill-color: currentColor; }
  button:not(:disabled):hover { background: #e9ede9; }
  button:focus-visible { outline: 2px solid var(--green); outline-offset: 2px; }
  .editor-header { background: var(--surface); border-bottom: 1px solid #e2e6e2; padding: 6px 16px; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; }
  .document-controls, .header-actions { display: flex; align-items: center; gap: 8px; min-width: 0; }
  .document-controls { flex: 1; }
  .header-actions { flex-shrink: 0; gap: 10px; }
  .back-button { width: 28px; height: 28px; border-radius: 50%; border: 1px solid var(--border); background: #f2f4f2; flex-shrink: 0; padding: 0; }
  .pill { border: 1px solid var(--border); border-radius: 999px; background: #f4f6f4; padding: 5px 13px; font-size: 10.5px; font-weight: 600; white-space: nowrap; }
  .branch { border-color: var(--accent-border); }
  .primary, .active { background: var(--green); color: white; border-color: var(--green); }
  .primary:not(:disabled):hover, .active:not(:disabled):hover { background: var(--accent-hover); }
  .document-meta { margin-left: 6px; min-width: 0; }
  .title-row { display: flex; align-items: center; gap: 8px; }
  .name { font-size: 12.5px; font-weight: 700; color: var(--text-h); margin: 0; line-height: 1.2; max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .save-status { font-size: 9px; color: var(--text-muted); white-space: nowrap; font-family: var(--mono); }
  .save-status span { color: var(--green); margin-right: 4px; }
  .menu-bar { display: flex; gap: 2px; margin-left: -6px; margin-top: 2px; }
  .menu-bar button { border: 0; background: transparent; padding: 2px 7px; border-radius: 4px; font-size: 11px; font-weight: 400; color: #202124; }
  .dropdown { position: relative; }
  .dropdown-panel { position: absolute; top: calc(100% + 5px); left: 0; z-index: 60; width: 205px; max-width: 80vw; padding: 5px; background: var(--surface); border: 1px solid var(--accent-border); border-radius: 9px; box-shadow: 0 12px 30px #19282226; }
  .dropdown-panel button, .menu-bar .dropdown-panel button { display: flex; justify-content: space-between; width: 100%; padding: 8px; border: 0; border-radius: 5px; background: transparent; text-align: left; font-size: 11px; }
  .dropdown-panel button:disabled { color: #78867f; }.dropdown-panel small { font-size: 8px; }
  .draft-panel { padding: 12px; }.draft-panel p { font-size: 10px; color: var(--text-muted); }
  .menu-bar .dropdown:last-child .dropdown-panel { left: auto; right: 0; }
  .editor-header { position: relative; z-index: 20; flex-shrink: 0; }

  
  

@media (max-width: 1023px) { .document-controls { flex-wrap: wrap; } .title-row { flex-wrap: wrap; } .header-actions { margin-left: auto; } }

@media (max-width: 560px) { .document-controls { flex: 1 0 100%; width: 100%; } .header-actions { margin-left: 0; } .editor-header { padding: 8px 12px; } .document-meta { flex-basis: 100%; margin: 4px 0 0; } .name { max-width: 240px; } .menu-bar { flex-wrap: wrap; } }
</style>
