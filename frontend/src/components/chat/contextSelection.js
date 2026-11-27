/**
 * Pure rules for the Assistant's Context selection (D-005, D-006, D-009).
 *
 * A selection is `{ web, manuscript, sourceIds }`. Web and Manuscript are independent of the
 * checked library entry IDs. When nothing is checked, Web is checked, so a selection is never
 * empty.
 *
 * @typedef {{ web: boolean, manuscript: boolean, sourceIds: string[] }} ContextSelection
 */

/** @returns {ContextSelection} The selection a new chat starts with: Web alone. */
export const initialSelection = () => ({ web: true, manuscript: false, sourceIds: [] });

/** @param {ContextSelection} selection */
function settle(selection) {
  return selection.manuscript || selection.sourceIds.length > 0 ? selection : { ...selection, web: true };
}

/** Check or uncheck Web. Unchecking the last checked item leaves Web checked. */
export const setWeb = (selection, on) => settle({ ...selection, web: on });

/** Check or uncheck Manuscript. Web keeps its setting unless nothing else stays checked. */
export const setManuscript = (selection, on) => settle({ ...selection, manuscript: on });

/** Check or uncheck one library source. Web keeps its setting unless nothing else stays checked. */
export function setSource(selection, id, on) {
  const rest = selection.sourceIds.filter((value) => value !== id);
  return settle({ ...selection, sourceIds: on ? [...rest, id] : rest });
}

/**
 * Check or uncheck every indexed source at once. Checking copies the IDs given, which are the
 * project's indexed sources right now, and keeps any other checked source. Web and Manuscript
 * are preserved.
 * @param {ContextSelection} selection
 * @param {string[]} indexedIds
 * @param {boolean} on
 */
export function setAllIndexed(selection, indexedIds, on) {
  if (!on) return settle({ ...selection, sourceIds: [] });
  const rest = selection.sourceIds.filter((value) => !indexedIds.includes(value));
  return { ...selection, sourceIds: [...rest, ...indexedIds] };
}

/** Return to Web alone. */
export const clearSelection = initialSelection;

/** True when at least one source is indexed and every indexed source is checked. */
export const allIndexedChecked = (selection, indexedIds) =>
  indexedIds.length > 0 && indexedIds.every((id) => selection.sourceIds.includes(id));

/**
 * Summarize the selection for the closed Context button, e.g. "Web" or "Manuscript + 2 sources".
 * @param {ContextSelection} selection
 */
export function summarize(selection) {
  const count = selection.sourceIds.length;
  const parts = [];
  if (selection.web) parts.push('Web');
  if (selection.manuscript) parts.push('Manuscript');
  if (count > 0) parts.push(`${count} ${count === 1 ? 'source' : 'sources'}`);
  return parts.join(' + ');
}

/**
 * Express a selection through the exchange request's existing fields. Web alone is scope `none`
 * with empty manuscript text and null source IDs. The draft is sent only when Manuscript is
 * checked.
 * @param {ContextSelection} selection
 * @param {string} draftText  The editor text at send time.
 * @returns {{ contextScope: 'none' | 'manuscript' | 'source_library', sourceIds: string[] | null, manuscriptText: string, web: boolean, manuscript: boolean }}
 */
export function encodeSelection(selection, draftText) {
  const { web, manuscript } = selection;
  const manuscriptText = manuscript ? draftText : '';
  if (selection.sourceIds.length > 0) {
    return { contextScope: 'source_library', sourceIds: [...selection.sourceIds], manuscriptText, web, manuscript };
  }
  if (manuscript) return { contextScope: 'manuscript', sourceIds: null, manuscriptText, web, manuscript };
  return { contextScope: 'none', sourceIds: null, manuscriptText: '', web, manuscript };
}

/**
 * Rebuild the selection a saved conversation was last successfully asked with. A record with
 * `web` and `manuscript` flags is used as saved. An older record maps from its scope: `none` is
 * Web alone, `manuscript` is Manuscript alone and `source_library` is its sources alone, where
 * null means every indexed source in `indexedIds`.
 * @param {{ context_scope?: string, web?: boolean, manuscript?: boolean, source_ids?: string[] | null }} conversation
 * @param {string[]} indexedIds
 * @returns {ContextSelection}
 */
export function selectionFromConversation(conversation, indexedIds = []) {
  if (typeof conversation.web === 'boolean' && typeof conversation.manuscript === 'boolean') {
    const everySource = conversation.context_scope === 'source_library' ? indexedIds : [];
    return settle({ web: conversation.web, manuscript: conversation.manuscript, sourceIds: [...(conversation.source_ids ?? everySource)] });
  }
  if (conversation.context_scope === 'manuscript') return { web: false, manuscript: true, sourceIds: [] };
  if (conversation.context_scope === 'source_library') {
    return settle({ web: false, manuscript: false, sourceIds: [...(conversation.source_ids ?? indexedIds)] });
  }
  return initialSelection();
}

/**
 * Restore a saved conversation's selection and name the saved sources that can no longer be
 * searched. Those are left out of the selection; every other choice is kept. Without
 * `indexedIds`, nothing is judged unavailable.
 * @param {Parameters<typeof selectionFromConversation>[0] & { sources?: { id: string, title: string }[] }} conversation
 * @param {string[] | null} indexedIds  The project's indexed source IDs now, or null if unknown.
 * @returns {{ selection: ContextSelection, unavailable: { id: string, title: string }[] }}
 */
export function restoreSelection(conversation, indexedIds = null) {
  const restored = selectionFromConversation(conversation, indexedIds ?? []);
  if (indexedIds === null) return { selection: restored, unavailable: [] };
  const titles = new Map((conversation.sources ?? []).map((source) => [source.id, source.title]));
  const missing = restored.sourceIds.filter((id) => !indexedIds.includes(id));
  return {
    selection: settle({ ...restored, sourceIds: restored.sourceIds.filter((id) => indexedIds.includes(id)) }),
    unavailable: missing.map((id) => ({ id, title: titles.get(id) || 'A saved source' })),
  };
}

