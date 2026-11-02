<script>
  import { getManuscript, saveManuscript } from "../lib/api/manuscripts.js";
  import { onMount } from "svelte";
  import { Editor } from "@tiptap/core";
  import ManuscriptCanvas from "../components/editor/ManuscriptCanvas.svelte";
  import EditorHeader from "../components/editor/EditorHeader.svelte";
  import SectionsSidebar from "../components/editor/SectionsSidebar.svelte";
  import EditorToolbar from "../components/editor/EditorToolbar.svelte";
  import ChatPanel from "../components/chat/ChatPanel.svelte";
  import { fonts, sizes, normalizeFontSize, InlineStyle, Underline, Alignment, PageBreak, SelectionHighlight } from "../lib/editor/extensions.js";
  import StarterKit from "@tiptap/starter-kit";

  let { id, onback } = $props();

  /* API INTEGRATION GUIDE
   * ACTIVE API: document load and save() below, plus ChatPanel.svelte send(), use the
   * existing backend. Keep their endpoints and payload contracts unchanged.
   * TODO(API): marks future integrations, not runnable request code.
   * Disabled controls remain visible to preserve the Theseus layout.
   * No endpoint names or response shapes are assumed for future features.
   * LOCAL ONLY: formatting, sections, manual page breaks, zoom, menus, and
   * citation text run in the browser. Document edits persist through save().
   */

  let element = $state.raw();
  let editor = $state.raw(null);
  let tick = $state(0);

  let open = $state(false);
  const wordCount = $derived.by(() => {
    tick;
    const text = editor?.getText().trim() ?? "";
    return text ? text.split(/\s+/).length : 0;
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
  function setFont(attribute, value, options = {}) {
    if (attribute === 'fontSize') {
      value = normalizeFontSize(value);
      if (!value) return;
    }
    if (!editor) return;
    let chain = editor.chain();
    if (options.selection) chain = chain.setTextSelection(options.selection);
    if (options.focus !== false) chain = chain.focus();
    chain.setMark('manuscriptStyle', { [attribute]: value }).run();
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
      extensions: [StarterKit.configure({ underline: false }), InlineStyle, Underline, Alignment, PageBreak, SelectionHighlight],
      content: "",
      onTransaction: () => tick++,
    });

    // ACTIVE API: GET the current document; response supplies doc.content.
    getManuscript(id)
      .then((r) => r.json())
      .then((doc) => editor.commands.setContent(doc.content));

    return () => { editor.destroy(); };
  });

  // ACTIVE API: POST /api/save with document_id and content (HTML).
  // TODO(API): Add persisted revision metadata or commit descriptions only after
  // the backend supports them. Do not add fields to this request speculatively.
  // TODO(API): Indexing/chunk progress needs real server job/status data.
  // A completed save request alone does not prove indexing is complete.
  async function save() {
    await saveManuscript(id, editor.getHTML());
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
  <EditorHeader {id} {editor} {onback} {menuItems} {runMenu} {save} {icon} bind:menuOpen bind:open />

  <EditorToolbar {editor} {fonts} {sizes} {fontFamily} {fontSize} {setFont} {tools} {active} {runMenu} {showDialog} {isAligned} {align} {outline} {currentPage} {jumpTo} {addPage} {zoom} {changeZoom} {wordCount} {icon} />

  {#if notice}<div class="local-notice" role="status"><span>{notice}</span><button type="button" onclick={() => notice = ''} aria-label="Dismiss notice">×</button></div>{/if}

  <div class="workspace">
    {#if showSections}<SectionsSidebar {editor} {outline} {currentSection} {showDialog} {sectionOnNextPage} {jumpTo} {wordCount} {icon} />{/if}

    <ManuscriptCanvas {zoom} pageCount={outline.length} bind:element />

    <ChatPanel {id} {editor} {tick} {open} onclose={() => open = false} bind:notice />
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
  .theseus-editor * { box-sizing: border-box; }
  button { font: inherit; color: inherit; margin: 0; }
  button { display: inline-flex; align-items: center; justify-content: center; gap: 6px; cursor: pointer; line-height: 1.3; }
  button:disabled { cursor: default; opacity: 1; -webkit-text-fill-color: currentColor; }
  button:not(:disabled):hover { background: #e9ede9; }
  button:focus-visible { outline: 2px solid var(--green); outline-offset: 2px; }
  .primary { background: var(--green); color: white; border-color: var(--green); }
  .primary:not(:disabled):hover { background: var(--accent-hover); }
  .workspace { flex: 1; min-height: 0; display: flex; overflow: hidden; }
  h3 { font-size: 9px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; margin: 0; }
  @media (max-width: 1023px) { .theseus-editor { height: auto; min-height: calc(100dvh - 48px); overflow: visible; }.workspace { flex-direction: column; overflow: visible; } }

  .local-notice { display: flex; justify-content: space-between; align-items: center; gap: 10px; background: #eff4ef; border-bottom: 1px solid var(--border); padding: 7px 16px; font-size: 11px; flex-shrink: 0; }.local-notice button { border: 0; background: transparent; }
  .input-dialog { width: min(380px, calc(100vw - 32px)); border: 1px solid var(--accent-border); border-radius: 12px; padding: 22px; background: var(--surface); color: var(--text); font: 12px var(--sans); box-shadow: 0 20px 60px #19282233; }.input-dialog::backdrop { background: #19282255; }.input-dialog h3 { font-size: 14px; margin-bottom: 16px; }.input-dialog label { display: grid; gap: 6px; }.input-dialog input { width: 100%; padding: 9px; border: 1px solid #aeb9b3; border-radius: 6px; background: white; color: var(--text); font: inherit; }.input-dialog p { color: var(--text-muted); line-height: 1.5; }.dialog-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 18px; }.dialog-actions button { border: 1px solid #aeb9b3; border-radius: 6px; padding: 7px 14px; }

</style>
