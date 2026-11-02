import { Plugin } from "@tiptap/pm/state";
import { Decoration, DecorationSet } from "@tiptap/pm/view";
import { Extension, Mark, Node, mergeAttributes } from "@tiptap/core";

// Local editor extensions serialize into the existing content HTML field.
// No new endpoints or request fields are used.
export function normalizeFontSize(value) {
  const match = String(value).trim().match(/^(\d+(?:\.\d+)?|\.\d+)(?:px)?$/);
  const size = match ? Number(match[1]) : NaN;
  return Number.isFinite(size) && size >= 1 && size <= 300 ? `${size}px` : null;
}

export const fonts = ['Times New Roman', 'Georgia', 'Inter', 'JetBrains Mono'];
export const sizes = ['12px', '14px', '16px', '18px', '20px', '24px', '28px', '32px'];
export const InlineStyle = Mark.create({
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
        parseHTML: el => normalizeFontSize(el.style.fontSize),
        renderHTML: attrs => attrs.fontSize ? { style: `font-size: ${attrs.fontSize}` } : {},
      },
    };
  },
  parseHTML() { return [{ tag: 'span[style]' }]; },
  renderHTML({ HTMLAttributes }) { return ['span', mergeAttributes(HTMLAttributes), 0]; },
});
export const Underline = Mark.create({
  name: 'underline',
  parseHTML() { return [{ tag: 'u' }, { style: 'text-decoration', consuming: false, getAttrs: value => value.includes('underline') ? {} : false }]; },
  renderHTML({ HTMLAttributes }) { return ['u', HTMLAttributes, 0]; },
  addKeyboardShortcuts() { return { 'Mod-u': () => this.editor.commands.toggleMark('underline') }; },
});
export const Alignment = Extension.create({
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
export const PageBreak = Node.create({
  name: 'manualPageBreak', group: 'block', atom: true, selectable: true,
  parseHTML() { return [{ tag: 'div[data-manual-page-break]' }]; },
  renderHTML() { return ['div', { 'data-manual-page-break': '', style: 'break-after: page;', contenteditable: 'false', 'aria-label': 'Manual page break' }]; },
  renderText() { return '\n\n'; },
});


// View-only highlight keeps the selected passage visible while toolbar inputs have focus.
// Decorations never become part of saved manuscript HTML.
export const SelectionHighlight = Extension.create({
  name: 'selectionHighlight',
  addProseMirrorPlugins() {
    return [new Plugin({ props: {
      decorations(state) {
        const { from, to, empty } = state.selection;
        return empty ? DecorationSet.empty : DecorationSet.create(state.doc, [
          Decoration.inline(from, to, { class: 'toolbar-selection' }),
        ]);
      },
    } })];
  },
});
