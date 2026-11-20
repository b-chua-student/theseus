import { test, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import {
  createTextSource,
  listTextSources,
  searchTextSources,
  getTextSource,
  updateTextSource,
  deleteTextSource,
  mapFieldErrors,
  TextSourceValidationError,
} from './textSources.js';

const P = '11111111-1111-4111-8111-111111111111';
const realFetch = globalThis.fetch;
/** @type {{url: string, init: any}[]} */
let calls;

/** @param {number} status @param {any} [body] @param {Record<string,string>} [headers] */
function mockFetch(status, body, headers = {}) {
  globalThis.fetch = async (url, init) => {
    calls.push({ url: String(url), init });
    return new Response(body === undefined ? null : JSON.stringify(body), { status, headers });
  };
}

beforeEach(() => {
  calls = [];
});
afterEach(() => {
  globalThis.fetch = realFetch;
});

test('createTextSource POSTs JSON with credentials and returns the DTO', async () => {
  const dto = { id: 'a1', kind: 'text', version: 1 };
  mockFetch(201, dto);
  const input = { title: 'T', content: 'hello', tags: ['x'] };
  assert.deepEqual(await createTextSource(P, input), dto);
  assert.equal(calls[0].url, `/api/sources/text?projectId=${P}`);
  assert.equal(calls[0].init.method, 'POST');
  assert.equal(calls[0].init.credentials, 'include');
  assert.equal(calls[0].init.headers['Content-Type'], 'application/json');
  assert.deepEqual(JSON.parse(calls[0].init.body), input);
});

test('listTextSources builds a query and omits empty params', async () => {
  mockFetch(200, { items: [], total: 0, page: 1, pageSize: 20 });
  await listTextSources(P, { contentType: 'notes', tag: '', sort: 'title', page: 2 });
  const qs = new URL(calls[0].url, 'http://x').searchParams;
  assert.equal(calls[0].url.startsWith('/api/sources/text?'), true);
  assert.equal(qs.get('contentType'), 'notes');
  assert.equal(qs.get('sort'), 'title');
  assert.equal(qs.get('page'), '2');
  assert.equal(qs.has('tag'), false);
  assert.equal(qs.get('projectId'), P);
});

test('listTextSources with no params has no query string', async () => {
  mockFetch(200, { items: [] });
  await listTextSources(P);
  assert.equal(calls[0].url, `/api/sources/text?projectId=${P}`);
});

test('searchTextSources hits /search and encodes q', async () => {
  mockFetch(200, { items: [] });
  await searchTextSources(P, { q: 'a&b c', tag: 't' });
  assert.equal(calls[0].url.startsWith('/api/sources/text/search?'), true);
  const sp = new URL(calls[0].url, 'http://x').searchParams;
  assert.equal(sp.get('q'), 'a&b c');
  assert.equal(sp.get('projectId'), P);
});

test('get, update and delete use the item URL with encoded id', async () => {
  mockFetch(200, { id: 'a/b' });
  await getTextSource(P, 'a/b');
  assert.equal(calls[0].url, `/api/sources/text/a%2Fb?projectId=${P}`);

  await updateTextSource(P, 'i1', { title: 'T', content: 'c' });
  assert.equal(calls[1].url, `/api/sources/text/i1?projectId=${P}`);
  assert.equal(calls[1].init.method, 'PUT');

  mockFetch(204);
  assert.equal(await deleteTextSource(P, 'i1'), undefined);
  assert.equal(calls.at(-1).init.method, 'DELETE');
  assert.equal(calls.at(-1).url, `/api/sources/text/i1?projectId=${P}`);
});

test('400 with errors becomes TextSourceValidationError with fieldErrors', async () => {
  mockFetch(400, {
    errors: [
      { field: 'title', message: 'too long' },
      { field: 'title', message: 'second ignored' },
      { field: 'content', message: 'required' },
    ],
  });
  await assert.rejects(createTextSource(P, { title: '', content: '' }), (e) => {
    assert.ok(e instanceof TextSourceValidationError);
    assert.ok(e && typeof e === 'object' && 'status' in e);
    assert.equal(e.status, 400);
    assert.deepEqual(e.fieldErrors, { title: 'too long', content: 'required' });
    return true;
  });
});

test('400 without field errors falls back to a plain error', async () => {
  mockFetch(400, { error: 'Bad body' });
  await assert.rejects(createTextSource(P, { title: 't', content: 'c' }), (e) => {
    assert.ok(e instanceof Error);
    assert.equal(e.message, 'Bad body');
    assert.ok(e && typeof e === 'object' && 'status' in e);
    assert.equal(e.status, 400);
    assert.equal(e instanceof TextSourceValidationError, false);
    return true;
  });
});

test('404 uses fallback message and status', async () => {
  mockFetch(404, undefined);
  await assert.rejects(getTextSource(P, 'x'), (e) => {
    assert.ok(e instanceof Error);
    assert.equal(e.message, 'Text source not found.');
    assert.ok(e && typeof e === 'object' && 'status' in e);
    assert.equal(e.status, 404);
    return true;
  });
});

test('429 exposes retryAfter seconds', async () => {
  mockFetch(429, { error: 'Slow down' }, { 'Retry-After': '30' });
  await assert.rejects(createTextSource(P, { title: 't', content: 'c' }), (e) => {
    assert.ok(e && typeof e === 'object' && 'status' in e);
    assert.equal(e.status, 429);
    assert.ok('retryAfter' in e);
    assert.equal(e.retryAfter, 30);
    return true;
  });
});

test('network failure gives a readable message', async () => {
  globalThis.fetch = async () => {
    throw new TypeError('Failed to fetch');
  };
  await assert.rejects(listTextSources(P), /Could not reach the server/);
});

test('mapFieldErrors ignores malformed payloads', () => {
  assert.equal(mapFieldErrors(null), null);
  assert.equal(mapFieldErrors({ errors: [{ field: 1 }] }), null);
  assert.equal(mapFieldErrors({}), null);
});

test('every call refuses to run without a projectId (no request is sent)', async () => {
  mockFetch(200, {});
  const calls6 = [
    () => createTextSource('', { title: 't', content: 'c' }),
    () => listTextSources(''),
    () => searchTextSources('', { q: 'x' }),
    () => getTextSource('', 'i'),
    () => updateTextSource('', 'i', { title: 't', content: 'c' }),
    () => deleteTextSource('', 'i'),
  ];
  for (const call of calls6) await assert.rejects(call(), /project is required/);
  assert.equal(calls.length, 0);
});