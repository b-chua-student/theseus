<script>
  import { onMount } from "svelte";
  import { Editor, Extension, Mark, Node, mergeAttributes } from "@tiptap/core";
  import StarterKit from "@tiptap/starter-kit";

  let { id, onback } = $props();

  /* API INTEGRATION GUIDE
   * ACTIVE API: document load, save(), and send() below already work with the
   * existing backend. Keep their endpoints and payload contracts unchanged.
   * TODO(API): marks future integrations, not runnable request code.
   * Disabled controls remain visible to preserve the Theseus layout.
   * No endpoint names or response shapes are assumed for future features.
   * LOCAL ONLY: formatting, sections, manual page breaks, zoom, menus, and
   * citation text run in the browser. Document edits persist through save().
   */

  let element;
  let editor = $state.raw(null);
  let tick = $state(0);

  let open = $state(false);
  let messages = $state([]);
  let input = $state("");
  let loading = $state(false);
  let log = $state();

  const wordCount = $derived.by(() => {
    tick;
    const text = editor?.getText().trim() ?? "";
    return text ? text.split(/\s+/).length : 0;
  });


  // Local editor extensions serialize into the existing content HTML field.
  // No new endpoints or request fields are used.
  const fonts = ['Times New Roman', 'Georgia', 'Inter', 'JetBrains Mono'];
  const sizes = ['12px', '14px', '16px', '18px', '20px', '24px', '28px', '32px'];
  const InlineStyle = Mark.create({
    name: 'manuscriptStyle',
    addAttributes() {
      return {
        fontFamily: {
          default: null,
          parseHTML: el => fonts.includes(el.style.fontFamily.replace(/["']/g, '')) ? el.style.fontFamily.replace(/["']/g, '') : null,
          renderHTML: attrs => attrs.fontFamily ? { style: `font-family: ${attrs.fontFamily}` } : {},
        },
        fontSize: {
          default: null,
          parseHTML: el => sizes.includes(el.style.fontSize) ? el.style.fontSize : null,
          renderHTML: attrs => attrs.fontSize ? { style: `font-size: ${attrs.fontSize}` } : {},
        },
      };
    },
    parseHTML() { return [{ tag: 'span[style]' }]; },
    renderHTML({ HTMLAttributes }) { return ['span', mergeAttributes(HTMLAttributes), 0]; },
  });
  const Underline = Mark.create({
    name: 'underline',
    parseHTML() { return [{ tag: 'u' }, { style: 'text-decoration', consuming: false, getAttrs: value => value.includes('underline') ? {} : false }]; },
    renderHTML({ HTMLAttributes }) { return ['u', HTMLAttributes, 0]; },
    addKeyboardShortcuts() { return { 'Mod-u': () => this.editor.commands.toggleMark('underline') }; },
  });
  const Alignment = Extension.create({
    name: 'manuscriptAlignment',
    addGlobalAttributes() {
      return [{ types: ['paragraph', 'heading'], attributes: {
        textAlign: { default: null,
          parseHTML: el => ['left', 'center', 'right', 'justify'].includes(el.style.textAlign) ? el.style.textAlign : null,
          renderHTML: attrs => attrs.textAlign ? { style: `text-align: ${attrs.textAlign}` } : {},
        },
      } }];
    },
  });
  const PageBreak = Node.create({
    name: 'manualPageBreak', group: 'block', atom: true, selectable: true,
    parseHTML() { return [{ tag: 'div[data-manual-page-break]' }]; },
    renderHTML() { return ['div', { 'data-manual-page-break': '', style: 'break-after: page;', contenteditable: 'false', 'aria-label': 'Manual page break' }]; },
    renderText() { return '\n\n'; },
  });

  let zoom = $state(100);
  let showSections = $state(true);
  let menuOpen = $state(null);
  let notice = $state('');
  let sectionDialog = $state(false);
  let sectionName = $state('');
  let citationDialog = $state(false);
  let citationText = $state('');
  let dialogElement = $state();
  const fontFamily = $derived((tick, editor?.getAttributes('manuscriptStyle').fontFamily || 'Times New Roman'));
  const fontSize = $derived((tick, editor?.getAttributes('manuscriptStyle').fontSize || '16px'));
  const outline = $derived.by(() => {
    tick;
    const pages = [{ number: 1, pos: 0, sections: [] }];
    if (!editor) return pages;
    editor.state.doc.forEach((node, pos) => {
      if (node.type.name === 'manualPageBreak') pages.push({ number: pages.length + 1, pos: pos + node.nodeSize, sections: [] });
      else if (node.type.name === 'heading') pages[pages.length - 1].sections.push({ pos, title: node.textContent || 'Untitled section', level: node.attrs.level });
    });
    return pages;
  });
  const currentPage = $derived.by(() => {
    tick;
    const pos = editor?.state.selection.from ?? 0;
    return outline.filter(page => page.pos <= pos).at(-1) || outline[0];
  });
  const currentSection = $derived.by(() => {
    tick;
    const pos = editor?.state.selection.from ?? 0;
    return currentPage.sections.filter(section => section.pos <= pos).at(-1) || null;
  });
  // TODO(FRONTEND): Export DOCX needs a serializer/download implementation;
  // a server endpoint is optional, not a requirement.
  // TODO(API): Comparing persisted revisions needs a real revision baseline.
  // TODO(FRONTEND): Unsaved-change comparison could instead use a local snapshot.
  // Keep Export DOCX and Check changes disabled until their implementation exists.
  const menuItems = {
    File: [{ label: 'Save manuscript', action: 'save' }, { label: 'Add page', action: 'page' }, { label: 'Export DOCX', disabled: true }],
    Edit: [{ label: 'Undo', action: 'undo' }, { label: 'Redo', action: 'redo' }, { label: 'Select all', action: 'selectAll' }],
    View: [{ label: 'Zoom in', action: 'zoomIn' }, { label: 'Zoom out', action: 'zoomOut' }, { label: 'Reset zoom', action: 'zoomReset' }, { label: 'Toggle sections', action: 'sections' }, { label: 'Toggle assistant', action: 'chat' }],
    Insert: [{ label: 'Section', action: 'section' }, { label: 'Page break at cursor', action: 'break' }, { label: 'Citation text', action: 'citation' }],
    Format: [{ label: 'Bold', action: 'bold' }, { label: 'Italic', action: 'italic' }, { label: 'Underline', action: 'underline' }, { label: 'Clear formatting', action: 'clear' }],
    Tools: [{ label: 'Word count', action: 'words' }, { label: 'Check changes', disabled: true }],
    Help: [{ label: 'Keyboard shortcuts', action: 'help' }],
  };

  function jumpTo(pos) {
    if (!editor) return;
    editor.chain().focus().setTextSelection(Math.min(pos + 1, editor.state.doc.content.size)).scrollIntoView().run();
  }
  function setFont(attribute, value) {
    editor?.chain().focus().setMark('manuscriptStyle', { [attribute]: value }).run();
  }
  function align(value) {
    editor?.chain().focus().updateAttributes('paragraph', { textAlign: value }).updateAttributes('heading', { textAlign: value }).run();
  }
  function isAligned(value) {
    tick;
    return (editor?.getAttributes('paragraph').textAlign || editor?.getAttributes('heading').textAlign || 'left') === value;
  }
  function changeZoom(delta) { zoom = Math.max(50, Math.min(150, zoom + delta)); }
  function showDialog(kind) {
    menuOpen = null;
    if (kind === 'section') { sectionName = ''; sectionDialog = true; }
    else { citationText = ''; citationDialog = true; }
    queueMicrotask(() => dialogElement?.showModal());
  }
  function closeDialog() {
    dialogElement?.close(); sectionDialog = false; citationDialog = false;
  }
  function addSection() {
    const title = sectionName.trim();
    if (!title || !editor) return;
    const nextPage = outline[currentPage.number];
    const pos = nextPage ? nextPage.pos - 1 : editor.state.doc.content.size;
    editor.chain().focus().insertContentAt(pos, [
      { type: 'heading', attrs: { level: 2 }, content: [{ type: 'text', text: title }] },
      { type: 'paragraph' },
    ]).run();
    closeDialog(); jumpTo(pos); notice = 'Section added. Save to keep your changes.';
  }
  function addPage() {
    if (!editor) return;
    const pos = editor.state.doc.content.size;
    editor.chain().focus().insertContentAt(pos, [{ type: 'manualPageBreak' }, { type: 'paragraph' }]).run();
    jumpTo(pos + 1); notice = 'Page added. Save to keep your changes.';
  }
  function insertBreak() {
    editor?.chain().focus().insertContent([{ type: 'manualPageBreak' }, { type: 'paragraph' }]).scrollIntoView().run();
    notice = 'Manual page break inserted.';
  }
  function sectionOnNextPage() {
    if (!editor || !currentSection) return;
    const pos = currentSection.pos;
    if (pos === currentPage.pos && currentPage.number > 1) { notice = 'This section already starts on a new page.'; return; }
    editor.chain().focus().insertContentAt(pos, { type: 'manualPageBreak' }).run();
    jumpTo(pos + 1); notice = 'Section starts on a new page. Following content moves with the section.';
  }
  // LOCAL ONLY: insert user-entered citation text without requesting sources.
  // TODO(API): For source-backed citations, connect the project's source records
  // and verified metadata once that backend contract exists.
  function insertCitation() {
    if (!editor || !citationText.trim()) return;
    editor.chain().focus().insertContent({ type: 'text', text: citationText.trim() }).run();
    closeDialog(); notice = 'Citation text inserted. Check the source details before saving.';
  }
  function runMenu(action) {
    menuOpen = null;
    if (action === 'save') save();
    else if (action === 'section' || action === 'citation') showDialog(action);
    else if (action === 'page') addPage();
    else if (action === 'break') insertBreak();
    else if (action === 'zoomIn') changeZoom(10);
    else if (action === 'zoomOut') changeZoom(-10);
    else if (action === 'zoomReset') zoom = 100;
    else if (action === 'sections') showSections = !showSections;
    else if (action === 'chat') open = !open;
    else if (action === 'words') notice = `${wordCount} words · ${outline.length} manual page(s) · ${outline.reduce((n, p) => n + p.sections.length, 0)} heading(s)`;
    else if (action === 'help') notice = 'Ctrl/Cmd+B: bold · Ctrl/Cmd+I: italic · Ctrl/Cmd+U: underline · Ctrl/Cmd+Z: undo · Escape: close menu';
    else if (action === 'underline') editor?.chain().focus().toggleMark('underline').run();
    else if (action === 'clear') editor?.chain().focus().unsetAllMarks().clearNodes().run();
    else if (action === 'selectAll') editor?.chain().focus().selectAll().run();
    else if (action === 'undo' || action === 'redo') editor?.chain().focus()[action]().run();
    else if (action === 'bold') editor?.chain().focus().toggleBold().run();
    else if (action === 'italic') editor?.chain().focus().toggleItalic().run();
  }
  function closeMenus(event) {
    if (!event.target.closest?.('.dropdown')) menuOpen = null;
  }
  function windowKey(event) { if (event.key === 'Escape') menuOpen = null; }

  const active = (name, attrs) => (tick, editor?.isActive(name, attrs));

  const tools = [
    { label: "Bold", name: "bold", run: (c) => c.toggleBold() },
    { label: "Italic", name: "italic", run: (c) => c.toggleItalic() },
    { label: "H1", name: "heading", attrs: { level: 1 }, run: (c) => c.toggleHeading({ level: 1 }) },
    { label: "H2", name: "heading", attrs: { level: 2 }, run: (c) => c.toggleHeading({ level: 2 }) },
    { label: "Bullets", name: "bulletList", run: (c) => c.toggleBulletList() },
    { label: "Numbered", name: "orderedList", run: (c) => c.toggleOrderedList() },
    { label: "Code", name: "codeBlock", run: (c) => c.toggleCodeBlock() },
    { label: "Undo", run: (c) => c.undo() },
    { label: "Redo", run: (c) => c.redo() },
  ];

  onMount(() => {
    editor = new Editor({
      element,
      extensions: [StarterKit.configure({ underline: false }), InlineStyle, Underline, Alignment, PageBreak],
      content: "",
      onTransaction: () => tick++,
    });

    // ACTIVE API: GET the current document; response supplies doc.content.
    fetch(`/api/documents/${id}`)
      .then((r) => r.json())
      .then((doc) => editor.commands.setContent(doc.content));

    return () => editor.destroy();
  });

  // ACTIVE API: POST /api/save with document_id and content (HTML).
  // TODO(API): Add persisted revision metadata or commit descriptions only after
  // the backend supports them. Do not add fields to this request speculatively.
  // TODO(API): Indexing/chunk progress needs real server job/status data.
  // A completed save request alone does not prove indexing is complete.
  async function save() {
    await fetch("/api/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ document_id: id, content: editor.getHTML() }),
    });
  }

  function scrollDown() {
    queueMicrotask(() => log && (log.scrollTop = log.scrollHeight));
  }

  // ACTIVE API: POST /api/chat with document_id, message, and document text.
  // TODO(API): None/Source Library scopes need an agreed server context contract.
  // Keep scope controls disabled; do not pretend a tab changes server grounding.
  async function send() {
    const text = input.trim();
    if (!text || loading) return;
    messages.push({ role: "user", text });
    input = "";
    loading = true;
    scrollDown();
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          document_id: id,
          message: text,
          document: editor.getText(),
        }),
      });
      const data = await res.json();
      messages.push({ role: "assistant", text: data.reply });
    } catch {
      messages.push({ role: "assistant", text: "Request failed." });
    }
    loading = false;
    scrollDown();
  }

  function onkey(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }
</script>

<!-- Shared font loading lives in index.html; theme tokens live in app.css. -->

<!-- Local controls share one Tiptap document. Save/Chat request contracts remain unchanged. -->
<svelte:window onclick={closeMenus} onkeydown={windowKey} />
{#snippet icon(name, size = 14)}
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    {#if name === 'back'}<path d="M19 12H5m7-7-7 7 7 7" />
    {:else if name === 'branch'}<circle cx="6" cy="18" r="3"/><circle cx="18" cy="6" r="3"/><path d="M6 3v12m12-6a9 9 0 0 1-9 9"/>
    {:else if name === 'merge'}<circle cx="6" cy="6" r="3"/><circle cx="18" cy="18" r="3"/><path d="M6 21V9a9 9 0 0 0 9 9"/>
    {:else if name === 'chevron'}<path d="m6 9 6 6 6-6"/>
    {:else if name === 'save'}<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2Z"/><path d="M17 21v-8H7v8M7 3v5h8"/>
    {:else if name === 'history'}<path d="M3 4v6h6M3.5 15a9 9 0 1 0 2-9L3 10M12 7v5l3 3"/>
    {:else if name === 'panel'}<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M15 3v18"/>
    {:else if name === 'send'}<path d="m22 2-7 20-4-9-9-4 20-7ZM22 2 11 13"/>
    {:else if name === 'bullets'}<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>
    {:else if name === 'numbered'}<path d="M10 6h11M10 12h11M10 18h11M3 4h2v5M3 9h4M3 14c3-2 4 1 2 2l-2 3h4"/>
    {:else if name === 'left'}<path d="M3 6h18M3 10h14M3 14h18M3 18h14"/>
    {:else if name === 'center'}<path d="M3 6h18M6 10h12M3 14h18M6 18h12"/>
    {:else if name === 'right'}<path d="M3 6h18M7 10h14M3 14h18M7 18h14"/>
    {:else if name === 'justify'}<path d="M3 6h18M3 10h18M3 14h18M3 18h18"/>
    {:else if name === 'zoom'}<circle cx="10" cy="10" r="6"/><path d="m15 15 6 6"/>
    {:else if name === 'close'}<path d="m6 6 12 12M18 6 6 18"/>
    {:else if name === 'document'}<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6M8 13h8M8 17h6"/>
    {/if}
  </svg>
{/snippet}

<div class="theseus-editor">
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

  <div class="formatting-bar" role="group" aria-label="Manuscript formatting">
    <div class="format-tools">
      <select class="font-select" aria-label="Font family" disabled={!editor} value={fontFamily} onchange={event => setFont('fontFamily', event.currentTarget.value)}>{#each fonts as font}<option value={font}>{font}</option>{/each}</select>
      <select aria-label="Font size" disabled={!editor} value={fontSize} onchange={event => setFont('fontSize', event.currentTarget.value)}>{#each sizes as size}<option value={size}>{size.replace('px', ' px')}</option>{/each}</select>
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
      {#each ['left', 'center', 'right', 'justify'] as alignment}
        <button type="button" class="format-button" class:active={isAligned(alignment)} disabled={!editor} onclick={() => align(alignment)} title={`${alignment} alignment`} aria-label={`${alignment} alignment`} aria-pressed={isAligned(alignment)}>{@render icon(alignment, 12)}</button>
      {/each}
    </div>
    <div class="page-tools">
      <div class="page-pill"><span>Pages:</span><div class="page-links">{#each outline as page}<button type="button" class:page-number={currentPage.number === page.number} onclick={() => jumpTo(page.pos)} aria-label={`Go to page ${page.number}`}>p.{page.number}</button>{/each}</div><button type="button" disabled={!editor} onclick={addPage} title="Append a manual page" aria-label="Add page">+</button></div>
      <div class="page-pill zoom"><button type="button" disabled={zoom <= 50} onclick={() => changeZoom(-10)} aria-label="Zoom out" title="Zoom out">{@render icon('zoom', 11)} −</button><span>{zoom}%</span><button type="button" disabled={zoom >= 150} onclick={() => changeZoom(10)} aria-label="Zoom in" title="Zoom in">{@render icon('zoom', 11)} +</button></div>
      <span class="word-count">{wordCount} words</span>
    </div>
  </div>

  {#if notice}<div class="local-notice" role="status"><span>{notice}</span><button type="button" onclick={() => notice = ''} aria-label="Dismiss notice">×</button></div>{/if}
  <div class="workspace">
    {#if showSections}<aside class="sections-panel" aria-label="Sections and pages">
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
    </aside>{/if}

    <main class="document-canvas" aria-label="Manuscript editor">
      <div class="document-sheet" style:zoom={zoom / 100}>
        <div class="paper-rule"></div>
        <!-- Tiptap remains the sole editable document and owns all saved content. -->
        <div class="editor-mount" bind:this={element}></div>
        <footer class="paper-footer"><span>{outline.length} manual page(s)</span><span>Manual page breaks</span></footer>
      </div>
    </main>

    {#if open}
      <aside class="chat" id="theseus-chat" aria-label="Theseus AI assistant">
        <div class="chat-top">
          <div class="chat-head"><div class="assistant-brand"><span class="brand-square"></span><h3>Theseus AI Assistant</h3></div><button type="button" class="icon-button" onclick={() => (open = false)} aria-label="Close assistant" title="Close assistant">{@render icon('panel')}</button></div>
          <!-- TODO(API): ASSISTANT CONTEXT AND SOURCE LIBRARY
               Load authorized source records and define how scope/source IDs reach chat.
               Upload/indexing needs its own supported backend operations.
               Existing send() always sends the current manuscript text. -->
          <div class="context-tabs" role="group" aria-label="Assistant context">
            <button type="button" disabled title="Context switching is not implemented">None</button><button type="button" class="selected" disabled title="Existing chat uses this manuscript">Manuscript</button><button type="button" disabled title="Source context is not implemented">Source Library</button>
          </div>
          <div class="context-card">Context: Current Manuscript</div>
        </div>
        <div class="log" bind:this={log} role="log" aria-live="polite" aria-label="Assistant conversation">
          {#if messages.length === 0}
            <div class="welcome-card"><span class="message-meta">THESEUS ASSISTANT</span><h4>Your research assistant</h4><p>Ask a question about your current manuscript.</p></div>
          {/if}
          <!-- The original messages have no id property. Unkeyed rendering avoids duplicate keys. -->
          {#each messages as m}
            <div class="msg {m.role}"><span class="message-meta">{m.role === 'user' ? 'You' : 'Theseus Assistant'}</span><div>{m.text}</div></div>
          {/each}
          {#if loading}<div class="msg assistant" role="status">Thinking…</div>{/if}
        </div>
        <div class="chat-bottom">
          <!-- LOCAL ONLY: These buttons fill the input. Only Send makes a request. -->
          <div class="quick-actions"><button type="button" onclick={() => input = 'Summarize the current manuscript.'}>Summarize manuscript</button><button type="button" onclick={() => input = 'Explain the key points in the current manuscript.'}>Explain key points</button></div>
          <div class="chat-input"><textarea rows="2" placeholder="Ask about your manuscript…" aria-label="Message the assistant" bind:value={input} onkeydown={onkey}></textarea><button type="button" class="send-button" onclick={send} disabled={loading} aria-label="Send message" title="Send">{@render icon('send')}</button></div>
        </div>
      </aside>
    {/if}
  </div>
</div>

{#if sectionDialog || citationDialog}
  <dialog bind:this={dialogElement} class="input-dialog" oncancel={closeDialog} aria-labelledby="editor-dialog-title">
    <form onsubmit={event => { event.preventDefault(); sectionDialog ? addSection() : insertCitation(); }}>
      <h3 id="editor-dialog-title">{sectionDialog ? 'Add section' : 'Insert citation text'}</h3>
      {#if sectionDialog}<label>Section heading<input bind:value={sectionName} maxlength="200" required placeholder="e.g., Methodology" /></label><p>Adds a heading and paragraph at the end of the current manual page.</p>
      {:else}<label>Citation<input bind:value={citationText} maxlength="1000" required placeholder="e.g., (Santos, 2026)" /></label><p>Inserts plain text at your cursor. Source lookup is unavailable.</p>{/if}
      <div class="dialog-actions"><button type="button" onclick={closeDialog}>Cancel</button><button type="submit" class="primary">{sectionDialog ? 'Add section' : 'Insert'}</button></div>
    </form>
  </dialog>
{/if}

<style>
  .theseus-editor { --green: var(--accent); width: 100%; height: calc(100dvh - 48px); min-height: 560px; display: flex; flex-direction: column; overflow: hidden; background: #e3eae5; color: var(--text); font-family: var(--sans); font-size: 11px; line-height: 1.4; text-align: left; }
  .theseus-editor *, .theseus-editor :global(.tiptap *) { box-sizing: border-box; }
  button, select, textarea { font: inherit; color: inherit; margin: 0; }
  button { display: inline-flex; align-items: center; justify-content: center; gap: 6px; cursor: pointer; line-height: 1.3; }
  button:disabled, select:disabled { cursor: default; opacity: 1; -webkit-text-fill-color: currentColor; }
  button:not(:disabled):hover { background: #e9ede9; }
  button:focus-visible, select:focus-visible, textarea:focus-visible { outline: 2px solid var(--green); outline-offset: 2px; }
  .editor-header { background: var(--surface); border-bottom: 1px solid #e2e6e2; padding: 6px 16px; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; }
  .document-controls, .header-actions { display: flex; align-items: center; gap: 8px; min-width: 0; }
  .document-controls { flex: 1; }
  .header-actions { flex-shrink: 0; gap: 10px; }
  .back-button { width: 28px; height: 28px; border-radius: 50%; border: 1px solid var(--border); background: #f2f4f2; flex-shrink: 0; padding: 0; }
  .pill { border: 1px solid var(--border); border-radius: 999px; background: #f4f6f4; padding: 5px 13px; font-size: 10.5px; font-weight: 600; white-space: nowrap; }
  .branch { border-color: var(--accent-border); }
  .primary, .active, .format-button.active { background: var(--green); color: white; border-color: var(--green); }
  .primary:not(:disabled):hover, .active:not(:disabled):hover, .send-button:not(:disabled):hover { background: var(--accent-hover); }
  .document-meta { margin-left: 6px; min-width: 0; }
  .title-row { display: flex; align-items: center; gap: 8px; }
  .name { font-size: 12.5px; font-weight: 700; color: var(--text-h); margin: 0; line-height: 1.2; max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .save-status { font-size: 9px; color: var(--text-muted); white-space: nowrap; font-family: var(--mono); }
  .save-status span { color: var(--green); margin-right: 4px; }
  .menu-bar { display: flex; gap: 2px; margin-left: -6px; margin-top: 2px; }
  .menu-bar button { border: 0; background: transparent; padding: 2px 7px; border-radius: 4px; font-size: 11px; font-weight: 400; color: #202124; }
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
  .workspace { flex: 1; min-height: 0; display: flex; overflow: hidden; }
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
  .document-canvas { flex: 1; min-width: 0; overflow: auto; padding: 28px 24px; background: var(--canvas); }
  .document-sheet { width: 100%; max-width: 540px; min-height: 700px; padding: 40px 44px; margin: 0 auto; display: flex; flex-direction: column; background: var(--paper); border: 1.5px solid var(--accent); box-shadow: 0 8px 26px -4px rgb(28 42 36 / 14%), 0 2px 6px -1px rgb(28 42 36 / 6%); }
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
  .chat { width: 285px; flex-shrink: 0; display: flex; flex-direction: column; min-height: 0; background: #f6f7f5; border-left: 1px solid var(--border); }
  .chat-top { padding: 14px 14px 0; }.chat-head { display: flex; justify-content: space-between; align-items: center; padding-bottom: 12px; margin-bottom: 12px; border-bottom: 1px solid #e4e8e4; gap: 8px; }
  .assistant-brand { display: flex; align-items: center; gap: 8px; }.assistant-brand h3 { font-size: 10px; }.brand-square { width: 20px; height: 20px; border-radius: 5px; background: var(--green); flex-shrink: 0; }.icon-button { border: 0; background: transparent; color: #5a6760; padding: 2px; }
  .context-tabs { display: grid; grid-template-columns: repeat(3, 1fr); background: #eff2ef; border: 1px solid var(--border); border-radius: 9px; padding: 2px; margin-bottom: 12px; }.context-tabs button { background: transparent; border: 0; border-radius: 7px; padding: 6px 2px; font-size: 9.5px; font-weight: 500; color: #495650; white-space: nowrap; }.context-tabs .selected { background: var(--green); color: white; font-weight: 600; }
  .context-card { background: #f2f4f1; border: 1px solid var(--border); border-radius: 10px; padding: 8px 12px; font-size: 9.5px; font-weight: 500; color: #2f3b35; }
  .log { flex: 1; min-height: 0; overflow-y: auto; padding: 14px; display: flex; flex-direction: column; gap: 12px; }
  .welcome-card, .msg { border: 1px solid #e2e6e2; border-radius: 12px; padding: 14px; background: white; box-shadow: 0 1px 3px rgb(0 0 0 / 2%); font-size: 10px; line-height: 1.55; overflow-wrap: anywhere; }.welcome-card h4 { font-size: 11px; margin: 6px 0; }.welcome-card p { margin: 0; color: var(--text-muted); }.message-meta { display: block; font: 8.5px var(--mono); color: #78867f; margin-bottom: 6px; }.msg { white-space: pre-wrap; }.msg.user { background: #e7eee8; align-self: flex-end; max-width: 92%; }.msg.assistant { align-self: stretch; }
  .chat-bottom { padding: 12px; border-top: 1px solid #e2e6e2; background: var(--surface); }.quick-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 8px; }.quick-actions button { background: #f2f4f2; border: 1px solid var(--border); border-radius: 6px; padding: 6px; font-size: 9.5px; font-weight: 600; }
  .chat-input { display: flex; align-items: center; gap: 6px; }.chat-input textarea { flex: 1; min-width: 0; resize: vertical; max-height: 160px; background: white; border: 1px solid var(--border); border-radius: 7px; padding: 6px 10px; font-size: 10px; line-height: 1.4; }.chat-input textarea::placeholder { color: #94a09a; }.send-button { width: 28px; height: 28px; flex-shrink: 0; border: 0; border-radius: 7px; background: var(--green); color: white; padding: 0; }.send-button:disabled { opacity: .55; cursor: wait; }
  @media (max-width: 1023px) { .theseus-editor { height: auto; min-height: calc(100dvh - 48px); overflow: visible; }.workspace { flex-direction: column; overflow: visible; }.sections-panel { width: 100%; border-right: 0; border-bottom: 1px solid var(--border); }.sections-body { padding: 12px 16px; }.section-actions { max-width: 240px; }.section-card { max-width: 280px; }.sections-footer { display: none; }.document-canvas { max-height: 75dvh; flex: auto; }.chat { width: 100%; height: 500px; border-left: 0; border-top: 1px solid var(--border); }.chat-top { flex-shrink: 0; }.document-controls { flex-wrap: wrap; }.title-row { flex-wrap: wrap; }.header-actions { margin-left: auto; } }
  @media (max-width: 560px) { .document-controls { flex: 1 0 100%; width: 100%; } .editor-header, .formatting-bar { padding: 8px 12px; }.document-meta { flex-basis: 100%; margin: 4px 0 0; }.name { max-width: 240px; }.menu-bar { flex-wrap: wrap; }.format-tools { gap: 4px; }.document-canvas { padding: 20px 12px; }.document-sheet { padding: 28px 22px; }.header-actions { margin-left: 0; }.page-tools { flex-wrap: wrap; } }

  .dropdown { position: relative; }
  .dropdown-panel { position: absolute; top: calc(100% + 5px); left: 0; z-index: 60; width: 205px; max-width: 80vw; padding: 5px; background: var(--surface); border: 1px solid var(--accent-border); border-radius: 9px; box-shadow: 0 12px 30px #19282226; }
  .dropdown-panel button, .menu-bar .dropdown-panel button { display: flex; justify-content: space-between; width: 100%; padding: 8px; border: 0; border-radius: 5px; background: transparent; text-align: left; font-size: 11px; }
  .dropdown-panel button:disabled { color: #78867f; }.dropdown-panel small { font-size: 8px; }
  .draft-panel { padding: 12px; }.draft-panel p { font-size: 10px; color: var(--text-muted); }
  .menu-bar .dropdown:last-child .dropdown-panel { left: auto; right: 0; }
  .editor-header { position: relative; z-index: 20; flex-shrink: 0; }.formatting-bar { flex-shrink: 0; }
  .page-links { display: flex; max-width: 150px; overflow-x: auto; gap: 3px; }
  .section-card { margin-bottom: 6px; border-color: var(--border); background: var(--surface); }.section-card.section-selected { border-color: var(--accent-border); background: #e7eee8; }.section-text strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .page-jump { padding: 2px 0; border: 0; background: transparent; }
  .local-notice { display: flex; justify-content: space-between; align-items: center; gap: 10px; background: #eff4ef; border-bottom: 1px solid var(--border); padding: 7px 16px; font-size: 11px; flex-shrink: 0; }.local-notice button { border: 0; background: transparent; }
  .editor-mount :global(.tiptap [data-manual-page-break]) { display: block; height: 56px; margin: 36px -44px; background: var(--canvas); border-top: 1px solid #aeb9b3; border-bottom: 1px solid #aeb9b3; position: relative; user-select: none; }
  .editor-mount :global(.tiptap [data-manual-page-break]::after) { content: 'MANUAL PAGE BREAK'; position: absolute; inset: 0; display: grid; place-items: center; font: 9px var(--sans); letter-spacing: .08em; color: var(--accent-border); }
  .editor-mount :global(.tiptap [data-manual-page-break].ProseMirror-selectednode) { outline: 2px solid var(--accent); }
  .input-dialog { width: min(380px, calc(100vw - 32px)); border: 1px solid var(--accent-border); border-radius: 12px; padding: 22px; background: var(--surface); color: var(--text); font: 12px var(--sans); box-shadow: 0 20px 60px #19282233; }.input-dialog::backdrop { background: #19282255; }.input-dialog h3 { font-size: 14px; margin-bottom: 16px; }.input-dialog label { display: grid; gap: 6px; }.input-dialog input { width: 100%; padding: 9px; border: 1px solid #aeb9b3; border-radius: 6px; background: white; color: var(--text); font: inherit; }.input-dialog p { color: var(--text-muted); line-height: 1.5; }.dialog-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 18px; }.dialog-actions button { border: 1px solid #aeb9b3; border-radius: 6px; padding: 7px 14px; }
  @media (max-width: 560px) { .editor-mount :global(.tiptap [data-manual-page-break]) { margin-left: -22px; margin-right: -22px; } }
</style>
