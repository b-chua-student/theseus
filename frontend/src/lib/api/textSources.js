/**
 * Text source API client (/api/sources/text).
 *
 * Typed against the DTOs in the source-CRUD design. Validation failures
 * (HTTP 400 `{errors:[{field,message}]}`) are thrown as
 * {@link TextSourceValidationError} carrying a `fieldErrors` map that forms can
 * bind directly. All other failures use the same Error shape as http.js
 * (`message`, `status`, `code`), plus `retryAfter` (seconds) on 429.
 */

import { jsonBody } from './http.js';

const BASE = '/api/sources/text';

/**
 * @typedef {'documentation'|'notes'|'code'|'other'} TextContentType
 * @typedef {'updatedAt'|'title'} TextSourceSort
 *
 * @typedef {Object} TextSourceInput
 * @property {string} title
 * @property {string} content
 * @property {string} [description]
 * @property {string[]} [tags]
 * @property {TextContentType} [contentType]
 *
 * @typedef {Object} TextSource  Detail DTO (includes content).
 * @property {string} id
 * @property {'text'} kind
 * @property {string} title
 * @property {string|null} description
 * @property {string[]} tags
 * @property {TextContentType} contentType
 * @property {string} content
 * @property {number} version
 * @property {string} createdAt
 * @property {string} updatedAt
 *
 * @typedef {Omit<TextSource, 'content'> & { snippet: string }} TextSourceSummary
 *
 * @typedef {Object} TextSourcePage
 * @property {TextSourceSummary[]} items
 * @property {number} total
 * @property {number} page
 * @property {number} pageSize
 *
 * @typedef {Object} ListParams
 * @property {TextContentType} [contentType]
 * @property {string} [tag]
 * @property {TextSourceSort} [sort]
 * @property {number} [page]
 * @property {number} [pageSize]
 *
 * @typedef {Object} SearchParams
 * @property {string} q
 * @property {TextContentType} [contentType]
 * @property {string} [tag]
 * @property {number} [page]
 * @property {number} [pageSize]
 */

/** Raised on HTTP 400 with per-field errors. */
export class TextSourceValidationError extends Error {
  /** @param {Record<string, string>} fieldErrors first message per field */
  constructor(fieldErrors, message = 'Please fix the highlighted fields.') {
    super(message);
    this.name = 'TextSourceValidationError';
    this.status = 400;
    this.fieldErrors = fieldErrors;
  }
}

/**
 * Convert the backend `errors` array to `{ [field]: message }` (first wins).
 * Returns null when the payload has no usable field errors.
 * @param {any} body
 * @returns {Record<string, string>|null}
 */
export function mapFieldErrors(body) {
  if (!body || !Array.isArray(body.errors)) return null;
  /** @type {Record<string, string>} */
  const out = {};
  for (const e of body.errors) {
    if (e && typeof e.field === 'string' && typeof e.message === 'string' && !(e.field in out)) {
      out[e.field] = e.message;
    }
  }
  return Object.keys(out).length ? out : null;
}

/**
 * @param {Record<string, string|number|undefined|null>} params
 * @returns {string} query string including leading "?" or ""
 */
function toQuery(params) {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') qs.set(k, String(v));
  }
  const s = qs.toString();
  return s ? `?${s}` : '';
}

/**
 * @param {string} url
 * @param {RequestInit | undefined} options
 * @param {string} fallbackMessage
 * @returns {Promise<any>}
 */
async function request(url, options, fallbackMessage) {
  let res;
  try {
    res = await fetch(url, { credentials: 'include', ...options });
  } catch {
    throw new Error('Could not reach the server. Check your connection and try again.');
  }
  if (res.ok) return res.status === 204 ? null : res.json();

  const body = await res.json().catch(() => ({}));
  if (res.status === 400) {
    const fieldErrors = mapFieldErrors(body);
    if (fieldErrors) throw new TextSourceValidationError(fieldErrors, body.error || undefined);
  }
  const err = Object.assign(new Error(body.error || fallbackMessage), {
    code: body.code,
    status: res.status,
  });
  if (res.status === 429) {
    const ra = Number(res.headers?.get?.('Retry-After'));
    throw Object.assign(err, { retryAfter: Number.isFinite(ra) ? ra : undefined });
  }
  throw err;
}

/**
 * Every text source endpoint is scoped by a required `?projectId=` (the backend
 * answers 400 without it), so each call takes the project id first.
 * @param {string} projectId
 * @returns {string}
 */
function requireProject(projectId) {
  if (typeof projectId !== 'string' || !projectId) throw new Error('A project is required.');
  return projectId;
}

/**
 * @param {string} projectId
 * @param {Record<string, string|number|undefined|null>} [params]
 */
function url(projectId, path = '', params = {}) {
  return BASE + path + toQuery({ ...params, projectId: requireProject(projectId) });
}

/** @param {string} id */
const itemPath = (id) => `/${encodeURIComponent(id)}`;

/**
 * @param {string} projectId
 * @param {TextSourceInput} input
 * @returns {Promise<TextSource>}
 */
export async function createTextSource(projectId, input) {
  return request(url(projectId), jsonBody('POST', input), 'Failed to create text source.');
}

/**
 * @param {string} projectId
 * @param {ListParams} [params]
 * @returns {Promise<TextSourcePage>}
 */
export async function listTextSources(projectId, { contentType, tag, sort, page, pageSize } = {}) {
  return request(
    url(projectId, '', { contentType, tag, sort, page, pageSize }),
    undefined,
    'Failed to load text sources.',
  );
}

/**
 * @param {string} projectId
 * @param {SearchParams} params
 * @returns {Promise<TextSourcePage>}
 */
export async function searchTextSources(projectId, { q, contentType, tag, page, pageSize }) {
  return request(
    url(projectId, '/search', { q, contentType, tag, page, pageSize }),
    undefined,
    'Failed to search text sources.',
  );
}

/**
 * @param {string} projectId
 * @param {string} id
 * @returns {Promise<TextSource>}
 */
export async function getTextSource(projectId, id) {
  return request(url(projectId, itemPath(id)), undefined, 'Text source not found.');
}

/**
 * Full replace of editable fields.
 * @param {string} projectId
 * @param {string} id
 * @param {TextSourceInput} input
 * @returns {Promise<TextSource>}
 */
export async function updateTextSource(projectId, id, input) {
  return request(url(projectId, itemPath(id)), jsonBody('PUT', input), 'Failed to update text source.');
}

/**
 * @param {string} projectId
 * @param {string} id
 * @returns {Promise<void>}
 */
export async function deleteTextSource(projectId, id) {
  await request(url(projectId, itemPath(id)), { method: 'DELETE' }, 'Failed to delete text source.');
}