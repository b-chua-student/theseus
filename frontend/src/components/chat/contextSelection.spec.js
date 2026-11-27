import { describe, it, expect } from 'vitest';
import {
  allIndexedChecked, clearSelection, encodeSelection, initialSelection, restoreSelection,
  selectionFromConversation, setAllIndexed, setManuscript, setSource, setWeb, summarize,
} from './contextSelection.js';

const web = { web: true, manuscript: false, sourceIds: [] };

describe('selection rules', () => {
  it('starts on Web alone', () => {
    expect(initialSelection()).toEqual(web);
  });

  it('keeps Web as it was when Manuscript or a source is checked or unchecked', () => {
    const off = { web: false, manuscript: false, sourceIds: ['a'] };
    expect(setManuscript(off, true).web).toBe(false);
    expect(setSource(web, 'a', true).web).toBe(true);
    expect(setSource(setSource(web, 'a', true), 'a', false)).toEqual(web);
  });

  it('returns to Web when the last checked item is unchecked, or on Clear selection', () => {
    expect(setSource({ web: false, manuscript: false, sourceIds: ['a'] }, 'a', false)).toEqual(web);
    expect(setManuscript({ web: false, manuscript: true, sourceIds: [] }, false)).toEqual(web);
    expect(setWeb(web, false)).toEqual(web);
    expect(clearSelection()).toEqual(web);
  });

  it('checks every indexed source, including ones a filter hides, and keeps Web and Manuscript', () => {
    const selection = setAllIndexed({ web: true, manuscript: true, sourceIds: [] }, ['a', 'b', 'c'], true);
    expect(selection).toEqual({ web: true, manuscript: true, sourceIds: ['a', 'b', 'c'] });
    expect(allIndexedChecked(selection, ['a', 'b', 'c'])).toBe(true);
  });

  it('clears the all-selected indicator when one source is unchecked and restores it when all are', () => {
    const all = setAllIndexed(web, ['a', 'b'], true);
    const some = setSource(all, 'b', false);
    expect(allIndexedChecked(some, ['a', 'b'])).toBe(false);
    expect(some.sourceIds).toEqual(['a']);
    expect(allIndexedChecked(setSource(some, 'b', true), ['a', 'b'])).toBe(true);
  });

  it('never reports all sources selected when none are indexed', () => {
    expect(allIndexedChecked(web, [])).toBe(false);
  });

  it('summarizes the selection for the closed button', () => {
    expect(summarize(web)).toBe('Web');
    expect(summarize({ web: false, manuscript: true, sourceIds: ['a', 'b'] })).toBe('Manuscript + 2 sources');
    expect(summarize({ web: true, manuscript: false, sourceIds: ['a'] })).toBe('Web + 1 source');
  });
});

describe('encodeSelection', () => {
  it('sends Web alone as scope none with empty manuscript text and null source IDs', () => {
    expect(encodeSelection(web, 'Draft')).toEqual({
      contextScope: 'none', sourceIds: null, manuscriptText: '', web: true, manuscript: false,
    });
  });

  it('sends the draft only when Manuscript is checked', () => {
    const withSources = { web: false, manuscript: false, sourceIds: ['a'] };
    expect(encodeSelection(withSources, 'Draft').manuscriptText).toBe('');
    expect(encodeSelection({ ...withSources, manuscript: true }, 'Draft').manuscriptText).toBe('Draft');
    expect(encodeSelection({ web: false, manuscript: true, sourceIds: [] }, 'Draft')).toMatchObject({
      contextScope: 'manuscript', sourceIds: null, manuscriptText: 'Draft',
    });
  });

  it('sends every selected source ID without limit', () => {
    const ids = Array.from({ length: 1001 }, (_, index) => `s${index}`);
    expect(encodeSelection({ web: false, manuscript: false, sourceIds: ids }, '').sourceIds).toHaveLength(1001);
  });
});

describe('restoring a saved conversation', () => {
  it('uses the saved Web, Manuscript and source selection', () => {
    expect(selectionFromConversation({ web: false, manuscript: true, source_ids: ['a'], context_scope: 'source_library' })).toEqual({
      web: false, manuscript: true, sourceIds: ['a'],
    });
  });

  it('shows an old scope none record as Web alone', () => {
    expect(selectionFromConversation({ context_scope: 'none', source_ids: null })).toEqual(web);
  });

  it('shows an old manuscript record as Manuscript alone', () => {
    expect(selectionFromConversation({ context_scope: 'manuscript', source_ids: null })).toEqual({
      web: false, manuscript: true, sourceIds: [],
    });
  });

  it('shows an old source library record as its sources alone', () => {
    expect(selectionFromConversation({ context_scope: 'source_library', source_ids: ['a'] })).toEqual({
      web: false, manuscript: false, sourceIds: ['a'],
    });
  });

  it('snapshots the indexed library for an old all-library record with no source list', () => {
    expect(selectionFromConversation({ context_scope: 'source_library', source_ids: null }, ['a', 'b']).sourceIds).toEqual(['a', 'b']);
    expect(selectionFromConversation({ web: false, manuscript: false, context_scope: 'source_library', source_ids: null }, ['a', 'b']).sourceIds).toEqual(['a', 'b']);
  });

  it('does not select every source for a new conversation on Web', () => {
    expect(selectionFromConversation({ web: true, manuscript: false, context_scope: 'none', source_ids: null }, ['a'])).toEqual(web);
  });

  it('names saved sources that are no longer indexed and keeps the other choices', () => {
    const saved = {
      web: true, manuscript: true, context_scope: 'source_library', source_ids: ['a', 'b'],
      sources: [{ id: 'a', title: 'Methods' }, { id: 'b', title: 'Replication' }],
    };
    expect(restoreSelection(saved, ['a'])).toEqual({
      selection: { web: true, manuscript: true, sourceIds: ['a'] },
      unavailable: [{ id: 'b', title: 'Replication' }],
    });
  });

  it('keeps every saved choice when the indexed sources are unknown', () => {
    const saved = { web: false, manuscript: false, context_scope: 'source_library', source_ids: ['a'] };
    expect(restoreSelection(saved, null)).toEqual({
      selection: { web: false, manuscript: false, sourceIds: ['a'] },
      unavailable: [],
    });
  });

  it('falls back to Web when every saved source is gone', () => {
    const saved = { web: false, manuscript: false, context_scope: 'source_library', source_ids: ['a'] };
    expect(restoreSelection(saved, []).selection).toEqual(web);
  });
});
