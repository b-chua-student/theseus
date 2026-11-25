/**
 * Bindings for the `@component` scenarios in specs/assistant/combined_context/gherkin.feature
 * (T-001). The `@service` and `@acceptance` scenarios are bound in pytest under
 * backend/tests/domain/assistant/features/.
 *
 * The real ChatPanel and API client run against an in-memory `fetch` and a stub editor.
 * The Context dropdown does not exist yet, so these tests assume this contract (D-005, D-009):
 *  - A button whose accessible name starts with "Context" opens the dropdown. Its text ends
 *    with the selection summary, for example "Web" or "Manuscript + 2 sources".
 *  - Checkboxes named "Web", "Manuscript", "All indexed sources" and one per source title.
 *  - A "Clear selection" button and a search box whose name contains "Filter".
 *  - The source checkboxes sit in a group named "Sources"; Web, Manuscript and Clear selection
 *    sit outside it.
 *  - Indexed sources come from GET /api/projects/:id/indexed-sources ({ source_ids }) joined
 *    with titles from GET /api/sources.
 *  - Exchange requests carry `quote`, `manuscript_text`, `source_ids` and `context_scope`.
 *  - Saved conversations carry `web`, `manuscript`, `source_ids` and `sources` ({ id, title }).
 */
import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, waitFor, cleanup } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import ChatPanel from './ChatPanel.svelte';
import { parseFeature, findStep } from '../../lib/testing/gherkin.js';

const FEATURE = resolve('../specs/assistant/combined_context/gherkin.feature');
const PROJECT = '11111111-1111-4111-8111-111111111111';
const OTHER_PROJECT = '22222222-2222-4222-8222-222222222222';
const SAVED = 'saved-1';
const NAMES = '((?:"[^"]+")(?:(?:, | and )"[^"]+")*)';
const quoted = (text) => [...text.matchAll(/"([^"]+)"/g)].map((match) => match[1]);
const sourceId = (title) => `src-${title.toLowerCase().replace(/\W+/g, '-')}`;

/** In-memory stand-in for the conversation, source and indexed-source endpoints. */
function fakeServer() {
  const state = {
    /** @type {{ id: string, title: string }[]} */ sources: [],
    /** @type {string[]} */ indexed: [],
    /** @type {any[]} */ conversations: [],
    /** @type {Map<string, any>} */ saved: new Map(),
    failNext: false,
    /** @type {{ conversationId: string, body: any }[]} */ exchanges: [],
    /** @type {string[]} */ started: [],
  };
  let seq = 0;
  const reply = (status, body) => ({ ok: status >= 200 && status < 300, status, headers: new Headers(), json: async () => body });

  async function fetch(url, init = {}) {
    const { pathname } = new URL(String(url), 'http://app');
    const method = (init.method ?? 'GET').toUpperCase();
    let match;
    if (pathname === '/api/sources') {
      return reply(200, state.sources.map(({ id, title }) => ({ id, kind: 'text', title, authors: [], year: null, file_ref: '' })));
    }
    if (/^\/api\/projects\/[^/]+\/indexed-sources$/.test(pathname)) return reply(200, { source_ids: state.indexed });
    if (/^\/api\/projects\/[^/]+\/conversations$/.test(pathname)) {
      if (method !== 'POST') return reply(200, state.conversations);
      const id = `c${++seq}`;
      state.started.push(id);
      return reply(201, { id });
    }
    if ((match = /^\/api\/projects\/[^/]+\/conversations\/([^/]+)\/exchanges$/.exec(pathname))) {
      state.exchanges.push({ conversationId: match[1], body: JSON.parse(init.body) });
      if (state.failNext) {
        state.failNext = false;
        return reply(502, { error: 'The assistant failed to answer.', code: 'assistant.model_error' });
      }
      return reply(201, { answer: 'Answer.', citations: [] });
    }
    if ((match = /^\/api\/projects\/[^/]+\/conversations\/([^/]+)$/.exec(pathname))) {
      const conversation = state.saved.get(match[1]);
      return conversation ? reply(200, conversation) : reply(404, { error: 'Not found' });
    }
    return reply(404, {});
  }
  return { state, fetch };
}

/** Stub of the Tiptap editor surface ChatPanel uses. */
function fakeEditor(initial) {
  let text = initial;
  let selection = { empty: true, from: 0, to: 0 };
  const chain = { focus: () => chain, insertContent: () => chain, run: () => true };
  return {
    getText: () => text,
    get state() {
      return { selection, doc: { textBetween: (from, to) => text.slice(from, to) } };
    },
    chain: () => chain,
    replace(from, to) { text = text.replace(from, to); },
    include(part) { if (!text.includes(part)) text = `${text} ${part}.`; },
    select(part) {
      const from = text.indexOf(part);
      selection = { empty: false, from, to: from + part.length };
    },
  };
}

/** Drives ChatPanel through the assumed Context dropdown. */
class Panel {
  constructor() {
    this.server = fakeServer();
    this.editor = fakeEditor('The study analysed 12 samples.');
    this.projectId = PROJECT;
    this.user = userEvent.setup();
    this.tick = 0;
    this.view = null;
  }

  addSource(title, { indexed = true } = {}) {
    this.server.state.sources.push({ id: sourceId(title), title });
    if (indexed) this.server.state.indexed.push(sourceId(title));
  }

  removeSource(title) {
    this.server.state.sources = this.server.state.sources.filter((source) => source.title !== title);
    this.server.state.indexed = this.server.state.indexed.filter((id) => id !== sourceId(title));
  }

  get titles() {
    return this.server.state.sources.map((source) => source.title);
  }

  async ui() {
    if (!this.view) {
      vi.stubGlobal('fetch', this.server.fetch);
      this.view = render(ChatPanel, {
        props: { projectId: this.projectId, editor: this.editor, tick: this.tick, open: true, onclose: vi.fn(), notice: '' },
      });
    }
    return this.view;
  }

  contextButton() {
    return screen.getByRole('button', { name: /^context/i });
  }

  isOpen() {
    return screen.queryByRole('checkbox', { name: 'Web' }) !== null;
  }

  async open() {
    await this.ui();
    if (!this.isOpen()) await this.user.click(this.contextButton());
    await screen.findByRole('checkbox', { name: 'Web' });
  }

  async close() {
    if (this.isOpen()) await this.user.keyboard('{Escape}');
  }

  async item(name) {
    await this.open();
    return screen.findByRole('checkbox', { name });
  }

  async setChecked(name, value) {
    const box = await this.item(name);
    if (!(box instanceof HTMLInputElement) || box.type !== 'checkbox') {
      throw new Error(`Expected "${name}" to be a checkbox`);
    }
    if (box.checked !== value) await this.user.click(box);
  }

  /** Check exactly `names`; Web stays checked only if listed. */
  async setExactly(names) {
    for (const name of names) await this.setChecked(name, true);
    for (const name of ['Web', 'Manuscript', ...this.titles]) {
      if (!names.includes(name)) await this.setChecked(name, false);
    }
  }

  async expectChecked(name, value) {
    const box = await this.item(name);
    if (value) expect(box).toBeChecked();
    else expect(box).not.toBeChecked();
  }

  async filter(text) {
    await this.open();
    const box = screen.getByRole('searchbox', { name: /filter/i });
    await this.user.clear(box);
    if (text) await this.user.type(box, text);
  }

  async send(text = 'What does the evidence show?') {
    await this.ui();
    await this.close();
    const before = this.server.state.exchanges.length;
    const box = screen.getByRole('textbox', { name: 'Message the assistant' });
    await this.user.clear(box);
    await this.user.type(box, text);
    await this.user.click(screen.getByRole('button', { name: 'Send message' }));
    await waitFor(() => expect(this.server.state.exchanges.length).toBe(before + 1));
    await waitFor(() => expect(screen.queryByText(/Theseus is thinking/)).toBeNull());
  }

  lastExchange() {
    const { exchanges } = this.server.state;
    expect(exchanges.length).toBeGreaterThan(0);
    return exchanges[exchanges.length - 1];
  }

  saveConversation(names) {
    const sources = names.filter((name) => name !== 'Web' && name !== 'Manuscript');
    const conversation = {
      id: SAVED,
      title: 'Saved chat',
      started_at: '2026-01-01T00:00:00+00:00',
      context_scope: 'source_library',
      web: names.includes('Web'),
      manuscript: names.includes('Manuscript'),
      source_ids: sources.map(sourceId),
      sources: sources.map((title) => ({ id: sourceId(title), title })),
      exchanges: [{ id: 'e1', query: 'Earlier question', answer: 'Earlier answer', asked_at: '2026-01-01T00:00:00+00:00' }],
    };
    this.server.state.saved.set(SAVED, conversation);
    this.server.state.conversations = [conversation];
  }

  async openSaved() {
    await this.ui();
    await this.close();
    const closedHistory = screen.queryByRole('button', { name: 'History', expanded: false });
    if (closedHistory) await this.user.click(closedHistory);
    await screen.findByRole('option', { name: 'Saved chat' });
    await this.user.click(screen.getByRole('button', { name: 'New chat' }));
    await this.user.selectOptions(screen.getByRole('combobox', { name: 'Saved conversations' }), SAVED);
    await waitFor(() => expect(screen.getByText('Earlier answer')).toBeInTheDocument());
  }
}

/** @type {[('Given' | 'When' | 'Then'), RegExp, (panel: Panel, ...args: string[]) => unknown][]} */
const steps = [
  // ---- Background ----
  ['Given', /I have a manuscript open in the editor with the Assistant chat panel/, (p) => expect(p.editor.getText()).not.toBe('')],
  ['Given', /my project has indexed library sources (.+)/, (p, names) => quoted(names).forEach((title) => p.addSource(title))],

  // ---- Given: selection ----
  ['Given', new RegExp(`${NAMES} are checked`), (p, names) => p.setExactly(quoted(names))],
  ['Given', new RegExp(`${NAMES} are checked in the open Context dropdown`), (p, names) => p.setExactly(quoted(names))],
  ['Given', new RegExp(`${NAMES} are checked and "([^"]+)" is (checked|unchecked)(?: in the Context dropdown)?`), async (p, names, other, state) => {
    for (const name of quoted(names)) await p.setChecked(name, true);
    await p.setChecked(other, state === 'checked');
  }],
  ['Given', /only "([^"]+)" is checked/, (p, name) => p.setExactly([name])],
  ['Given', new RegExp(`I selected ${NAMES}`), async (p, names) => {
    for (const name of quoted(names)) await p.setChecked(name, true);
  }],
  ['Given', /"Web" is (checked|unchecked) in the Context dropdown/, async (p, state) => {
    if (state === 'checked') return p.setChecked('Web', true);
    await p.setChecked('Pilot', true);
    await p.setChecked('Web', false);
  }],
  ['Given', /keyboard focus is on the unchecked "([^"]+)" item/, async (p, name) => {
    const box = await p.item(name);
    expect(box).not.toBeChecked();
    box.focus();
  }],
  ['Given', /the open dropdown has more sources than fit onscreen/, async (p) => {
    for (let index = p.titles.length; index < 40; index += 1) p.addSource(`Source ${String(index).padStart(2, '0')}`);
    await p.open();
  }],
  ['Given', /only "([^"]+)" matches my title filter/, async (p, name) => {
    await p.filter(name);
    for (const title of p.titles.filter((title) => title !== name)) {
      expect(screen.queryByRole('checkbox', { name: title })).toBeNull();
    }
  }],
  ['Given', /I switch to a project with no indexed sources/, (p) => {
    p.projectId = OTHER_PROJECT;
    p.server.state.sources = [];
    p.server.state.indexed = [];
  }],
  ['Given', /I start a new chat/, (p) => p.ui()],

  // ---- Given: draft, quote and history ----
  ['Given', /I changed "([^"]+)" to "([^"]+)" in the draft without saving/, (p, from, to) => p.editor.replace(from, to)],
  ['Given', /I quoted "([^"]+)" from the editor/, async (p, quote) => {
    await p.ui();
    p.editor.include(quote);
    p.editor.select(quote);
    p.tick += 1;
    await p.view.rerender({ tick: p.tick });
    await p.close();
    await p.user.click(await screen.findByRole('button', { name: 'Quote selection' }));
  }],
  ['Given', /I asked a question with only "([^"]+)" checked/, async (p, name) => {
    await p.setExactly([name]);
    await p.send('First question');
  }],
  ['Given', /I cleared the selection and asked a second question/, async (p) => {
    await p.open();
    await p.user.click(screen.getByRole('button', { name: 'Clear selection' }));
    await p.send('Second question');
  }],
  ['Given', new RegExp(`my last successful exchange used ${NAMES}`), async (p, names) => {
    p.saveConversation(quoted(names));
  }],
  ['Given', /I then unchecked "([^"]+)" and checked "([^"]+)"/, async (p, off, on) => {
    await p.openSaved();
    await p.setChecked(off, false);
    await p.setChecked(on, true);
  }],
  ['Given', /my next question failed/, async (p) => {
    p.server.state.failNext = true;
    await p.send('A question that fails');
  }],
  ['Given', /"([^"]+)" has since been removed from the library/, (p, name) => p.removeSource(name)],

  // ---- When ----
  ['When', /I check "([^"]+)" in the same dropdown/, (p, name) => p.setChecked(name, true)],
  ['When', /I check "All indexed sources" in the Context dropdown/, (p) => p.setChecked('All indexed sources', true)],
  ['When', new RegExp(`I check ${NAMES}`), async (p, names) => {
    for (const name of quoted(names)) await p.setChecked(name, true);
  }],
  ['When', /I uncheck "([^"]+)"/, (p, name) => p.setChecked(name, false)],
  ['When', /I uncheck "([^"]+)" and send my next question/, async (p, name) => {
    await p.setChecked(name, false);
    await p.send('Next question');
  }],
  ['When', /I check "([^"]+)" and ask a third question/, async (p, name) => {
    await p.setChecked(name, true);
    await p.send('Third question');
  }],
  ['When', /I toggle "([^"]+)"/, async (p, name) => p.user.click(await p.item(name))],
  ['When', /I activate "Clear selection" in the Context dropdown/, async (p) => {
    await p.open();
    await p.user.click(screen.getByRole('button', { name: 'Clear selection' }));
  }],
  ['When', /I press Space and then Escape/, async (p) => {
    await p.user.keyboard(' ');
    await p.user.keyboard('{Escape}');
  }],
  ['When', /I filter for "([^"]+)", check it, and clear the filter/, async (p, name) => {
    await p.filter(name);
    await p.setChecked(name, true);
    await p.filter('');
  }],
  ['When', /I open the Context dropdown/, (p) => p.open()],
  ['When', /I send "([^"]+)"/, (p, text) => p.send(text)],
  ['When', /I send my question/, (p) => p.send()],
  ['When', /I send a question without changing context/, (p) => p.send()],
  ['When', /I reopen that chat from the saved conversations/, (p) => p.openSaved()],

  // ---- Then: checkbox state ----
  ['Then', new RegExp(`${NAMES} are checked`), async (p, names) => {
    for (const name of quoted(names)) await p.expectChecked(name, true);
  }],
  ['Then', new RegExp(`${NAMES} are unchecked`), async (p, names) => {
    for (const name of quoted(names)) await p.expectChecked(name, false);
  }],
  ['Then', new RegExp(`${NAMES} are (?:both|still) checked`), async (p, names) => {
    for (const name of quoted(names)) await p.expectChecked(name, true);
  }],
  ['Then', new RegExp(`${NAMES} remain checked`), async (p, names) => {
    for (const name of quoted(names)) await p.expectChecked(name, true);
  }],
  ['Then', new RegExp(`${NAMES} are selected`), async (p, names) => {
    await p.filter('');
    for (const name of quoted(names)) await p.expectChecked(name, true);
  }],
  ['Then', new RegExp(`${NAMES} are checked when I reopen it`), async (p, names) => {
    for (const name of quoted(names)) await p.expectChecked(name, true);
  }],
  ['Then', /"([^"]+)" is (checked|unchecked)/, (p, name, state) => p.expectChecked(name, state === 'checked')],
  ['Then', /"([^"]+)" is still (checked|unchecked)/, (p, name, state) => p.expectChecked(name, state === 'checked')],
  ['Then', /only "Web" is checked/, async (p) => {
    await p.expectChecked('Web', true);
    for (const name of ['Manuscript', ...p.titles]) await p.expectChecked(name, false);
  }],
  ['Then', /"All indexed sources" is the only checkbox for selecting sources in bulk/, async (p) => {
    await p.open();
    expect(screen.getAllByRole('checkbox', { name: /\ball\b/i })).toHaveLength(1);
    expect(screen.getByRole('checkbox', { name: 'All indexed sources' })).toBeInTheDocument();
  }],
  ['Then', /"All indexed sources" is disabled/, async (p) => expect(await p.item('All indexed sources')).toBeDisabled()],
  ['Then', new RegExp(`${NAMES} remain available`), async (p, names) => {
    for (const name of quoted(names)) expect(await p.item(name)).toBeEnabled();
  }],

  // ---- Then: dropdown layout and keyboard ----
  ['Then', /the dropdown closes with focus on the Context button/, (p) => {
    expect(p.isOpen()).toBe(false);
    expect(document.activeElement).toBe(p.contextButton());
  }],
  ['Then', new RegExp(`${NAMES} remain visible while I scroll the sources`), async (p, names) => {
    await p.open();
    const list = screen.getByRole('group', { name: 'Sources' });
    for (const name of quoted(names)) {
      const control = name === 'Clear selection'
        ? screen.getByRole('button', { name })
        : screen.getByRole('checkbox', { name });
      expect(control).toBeVisible();
      expect(list.contains(control)).toBe(false);
    }
  }],
  ['Then', /the closed button reads "([^"]+)"/, async (p, summary) => {
    await p.close();
    expect(p.contextButton().textContent.trim().endsWith(summary)).toBe(true);
  }],
  ['Then', /the Context button displays "([^"]+)"/, (p, summary) => {
    expect(p.contextButton().textContent.replace(/^\s*context:?/i, '').trim()).toBe(summary);
  }],
  ['Then', /the Assistant names "([^"]+)" as unavailable/, async (p, name) => {
    const notes = await screen.findAllByText((_, element) => {
      const text = element?.textContent ?? '';
      return element?.children.length === 0 && text.includes(name) && /unavailable/i.test(text);
    });
    expect(notes.length).toBeGreaterThan(0);
  }],

  // ---- Then: exchanges ----
  ['Then', /the exchange includes the current manuscript text/, (p) => {
    expect(p.lastExchange().body.manuscript_text).toBe(p.editor.getText());
  }],
  ['Then', /the selected source IDs contain only the ID of "([^"]+)"/, (p, name) => {
    expect(p.lastExchange().body.source_ids).toEqual([sourceId(name)]);
  }],
  ['Then', /the exchange belongs to the same conversation/, (p) => {
    expect(p.server.state.started).toHaveLength(1);
    expect(p.lastExchange().conversationId).toBe(p.server.state.started[0]);
  }],
  ['Then', /one exchange includes the current editor text containing "([^"]+)"/, (p, text) => {
    expect(p.server.state.exchanges).toHaveLength(1);
    expect(p.lastExchange().body.manuscript_text).toBe(p.editor.getText());
    expect(p.lastExchange().body.manuscript_text).toContain(text);
  }],
  ['Then', new RegExp(`its selected source IDs are exactly those of ${NAMES}`), (p, names) => {
    expect([...p.lastExchange().body.source_ids].sort()).toEqual(quoted(names).map(sourceId).sort());
  }],
  ['Then', /all three exchanges belong to the same conversation/, (p) => {
    const ids = p.server.state.exchanges.map((exchange) => exchange.conversationId);
    expect(ids).toHaveLength(3);
    expect(new Set(ids).size).toBe(1);
  }],
  ['Then', /the request uses scope "none" with empty manuscript text and null source IDs/, (p) => {
    const { body } = p.lastExchange();
    expect(body.context_scope).toBe('none');
    expect(body.manuscript_text).toBe('');
    expect(body.source_ids).toBeNull();
  }],
];

const scenarios = parseFeature(readFileSync(FEATURE, 'utf8')).filter((scenario) => scenario.tags.includes('component'));

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('combined context @component step bindings', () => {
  it('binds every step to exactly one definition', () => {
    expect(scenarios.length).toBeGreaterThan(0);
    for (const scenario of scenarios) for (const step of scenario.steps) findStep(steps, step);
  });
});

describe('Feature: Compare manuscript claims with selected library sources (@component)', () => {
  for (const scenario of scenarios) {
    const id = scenario.tags.find((tag) => /^S-\d{3}$/.test(tag));
    it(`${id} ${scenario.name}`, async () => {
      const panel = new Panel();
      for (const step of scenario.steps) {
        const { run, args } = findStep(steps, step);
        await run(panel, ...args);
      }
    });
  }
});
