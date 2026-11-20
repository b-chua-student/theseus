/**
 * Bindings for the `@ui`, `@accessibility` and `@responsive` scenarios in
 * .kiro/specs/source-CRUD/source_library_text_upload.feature.
 *
 * These run at component level (vitest + jsdom). The real SourceLibrary,
 * TextSourceForm/List and API client are used; only `fetch` is replaced by a
 * small in-memory server that enforces the backend contract this UI depends on
 * (required `?projectId=`, 400 field errors, DTOs with createdAt/updatedAt).
 * jsdom has no layout engine, so the responsive scenario checks the CSS rules
 * that make the layout fit rather than measuring rendered widths.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, cleanup } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { createRawSnippet } from 'svelte';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import SourceLibrary from '../dashboard/SourceLibrary.svelte';

const PROJECT = '11111111-1111-4111-8111-111111111111';
const icon = createRawSnippet(() => ({ render: () => '<span></span>' }));

/** In-memory stand-in for /api/sources and /api/sources/text. */
function fakeServer() {
  /** @type {Map<string, any>} */
  const store = new Map();
  /** @type {{method: string, path: string, projectId: string|null}[]} */
  const requests = [];
  let seq = 0;
  const reply = (status, body) => ({
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers(),
    json: async () => body,
  });
  // Stored records carry projectId; DTOs (like the backend's) do not.
  const dto = (s) => Object.fromEntries(Object.entries(s).filter(([k]) => k !== 'projectId'));
  const summary = (s) => {
    const { content, ...rest } = dto(s);
    return { ...rest, snippet: content.slice(0, 200) };
  };

  async function fetch(url, init = {}) {
    const u = new URL(String(url), 'http://app');
    const method = init.method ?? 'GET';
    const projectId = u.searchParams.get('projectId');
    requests.push({ method, path: u.pathname, projectId });

    if (u.pathname === '/api/sources') return reply(200, []);
    if (!u.pathname.startsWith('/api/sources/text')) return reply(404, {});
    if (!projectId) return reply(400, { errors: [{ field: 'projectId', message: 'projectId is required' }] });

    const id = decodeURIComponent(u.pathname.slice('/api/sources/text/'.length));
    if (u.pathname === '/api/sources/text' && method === 'POST') {
      const body = JSON.parse(init.body);
      const now = new Date().toISOString();
      const created = {
        id: `t${++seq}`, kind: 'text', title: body.title, description: body.description ?? null,
        tags: body.tags ?? [], contentType: body.contentType ?? 'other', content: body.content,
        version: 1, createdAt: now, updatedAt: now,
      };
      store.set(created.id, { ...created, projectId });
      return reply(201, dto(store.get(created.id)));
    }
    if (u.pathname === '/api/sources/text' && method === 'GET') {
      const items = [...store.values()].filter((s) => s.projectId === projectId).map(summary);
      return reply(200, { items, total: items.length, page: 1, pageSize: 20 });
    }
    const found = store.get(id);
    if (!found || found.projectId !== projectId) return reply(404, { error: 'Text source not found.' });
    return reply(200, dto(found));
  }
  return { fetch, store, requests };
}

let server;
beforeEach(() => {
  localStorage.clear();
  server = fakeServer();
  vi.stubGlobal('fetch', server.fetch);
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

// Background: I am on the source library text upload page.
async function openUploadPage(user) {
  const view = render(SourceLibrary, { icon, projectId: PROJECT });
  await user.click(await screen.findByRole('button', { name: '+ Add text' }));
  await screen.findByRole('form', { name: 'New text source' });
  return view;
}

describe('@create @ui', () => {
  it('Scenario: Character counter updates as I type', async () => {
    const user = userEvent.setup();
    await openUploadPage(user);
    await user.type(screen.getByLabelText('Content'), 'Hello');
    expect(screen.getByText('5 / 100,000')).toBeInTheDocument();
  });

  it('Scenario: Preview content before saving', async () => {
    const user = userEvent.setup();
    await openUploadPage(user);
    await user.type(screen.getByLabelText('Title'), 'API Spec v1');
    await user.type(screen.getByLabelText('Content'), "<b>bold?</b> GET /users");

    await user.click(screen.getByRole('button', { name: 'Preview' }));
    const preview = screen.getByLabelText('Preview');
    expect(preview.tagName).toBe('PRE');
    expect(preview).toHaveTextContent('<b>bold?</b> GET /users');
    expect(preview.querySelector('b')).toBeNull();
    expect(screen.queryByRole('textbox', { name: 'Content' })).toBeNull();
    expect(server.store.size).toBe(0);

    await user.click(screen.getByRole('button', { name: 'Create' }));
    // Saved: back on the list, with the new source shown.
    expect(await screen.findByText('API Spec v1')).toBeInTheDocument();
    const [saved] = server.store.values();
    expect(saved).toMatchObject({ title: 'API Spec v1', content: '<b>bold?</b> GET /users', version: 1, projectId: PROJECT });
    expect(saved.createdAt).toBeTruthy();
  });

  it('Scenario: Draft is auto-saved', async () => {
    const user = userEvent.setup();
    const first = await openUploadPage(user);
    await user.type(screen.getByLabelText('Title'), 'Half done');
    await user.type(screen.getByLabelText('Content'), 'Partial con');
    await waitFor(() => expect(localStorage.length).toBe(1), { timeout: 2000 });

    first.unmount(); // leave the page
    await openUploadPage(user); // return

    expect(screen.getByText(/Draft restored/)).toBeInTheDocument();
    expect(screen.getByLabelText('Title')).toHaveValue('Half done');
    expect(screen.getByLabelText('Content')).toHaveValue('Partial con');
    expect(server.store.size).toBe(0);
  });
});

describe('@accessibility @ui', () => {
  it('Scenario: Upload interface is accessible', async () => {
    const user = userEvent.setup();
    await openUploadPage(user);

    // Form fields have associated labels.
    const fields = ['Title', 'Type', 'Description (optional)', /^Tags/, 'Content'].map((l) => screen.getByLabelText(l));

    // All fields and buttons are reachable with the keyboard alone.
    const targets = [...fields, ...['Preview', 'Create', 'Cancel'].map((n) => screen.getByRole('button', { name: n }))];
    const reached = new Set();
    document.body.focus();
    for (let i = 0; i < 20 && reached.size < targets.length; i++) {
      await user.tab();
      const active = document.activeElement;
      if (active instanceof HTMLElement && targets.includes(active)) reached.add(active);
    }
    expect(reached.size).toBe(targets.length);

    // Submitting the empty form via the keyboard announces the errors.
    screen.getByRole('button', { name: 'Create' }).focus();
    await user.keyboard('{Enter}');
    const live = screen.getAllByRole('status').find((el) => el.getAttribute('aria-live') === 'polite');
    await waitFor(() => expect(live).toHaveTextContent('The form has 2 errors'));
    expect(screen.getByLabelText('Title')).toHaveAccessibleDescription('Title is required.');
    expect(server.requests.some((r) => r.method === 'POST')).toBe(false);
  });
});

describe('@responsive @ui Scenario Outline: Interface adapts to screen size', () => {
  const css = ['TextSourceForm', 'TextSourceList', 'TextSourceCard']
    .map((c) => readFileSync(resolve('src/components/text-sources', `${c}.svelte`), 'utf8'))
    .join('\n');
  // Declarations only; media query conditions like `(min-width: 768px)` are excluded.
  const fixedWidths = [...css.matchAll(/(?<![-\w(])(?:min-)?width:\s*(\d+)px/g)].map((m) => Number(m[1]));

  it.each([
    ['mobile', 375],
    ['tablet', 768],
    ['desktop', 1280],
  ])('Example: %s (%ipx) is usable without horizontal scrolling', (_device, viewport) => {
    // No element is forced wider than the viewport.
    expect(fixedWidths.filter((w) => w > viewport)).toEqual([]);
    // Long unbroken content wraps instead of overflowing.
    expect(css).toMatch(/overflow-wrap:\s*anywhere/);
    // Single column below tablet width; two columns from 768px.
    if (viewport < 768) expect(css).toMatch(/grid-template-columns:\s*1fr;/);
    else expect(css).toMatch(/@media \(min-width: 768px\)[\s\S]*grid-template-columns:\s*minmax\(0, 1fr\) minmax\(0, 2fr\)/);
  });
});

describe('project scoping (integration with the backend contract)', () => {
  it('every text source request carries the selected projectId, including open-for-edit', async () => {
    const user = userEvent.setup();
    await openUploadPage(user);
    await user.type(screen.getByLabelText('Title'), 'Scoped');
    await user.type(screen.getByLabelText('Content'), 'body');
    await user.click(screen.getByRole('button', { name: 'Create' }));
    await user.click(await screen.findByRole('button', { name: /Edit Scoped/ }));
    expect(await screen.findByRole('form', { name: 'Edit text source' })).toBeInTheDocument();
    expect(screen.getByLabelText('Content')).toHaveValue('body');

    const textCalls = server.requests.filter((r) => r.path.startsWith('/api/sources/text'));
    expect(textCalls.map((r) => r.method)).toEqual(expect.arrayContaining(['GET', 'POST']));
    expect(textCalls.every((r) => r.projectId === PROJECT)).toBe(true);
  });

  it('without a selected project, no text source request is sent', async () => {
    render(SourceLibrary, { icon, projectId: '' });
    await waitFor(() => expect(server.requests.some((r) => r.path === '/api/sources')).toBe(true));
    expect(screen.queryByRole('button', { name: '+ Add text' })).toBeNull();
    expect(server.requests.some((r) => r.path.startsWith('/api/sources/text'))).toBe(false);
  });
});
