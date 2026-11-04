/**
 * Drafts API client.
 * All requests are scoped under
 * /api/projects/:projectId/manuscripts/:manuscriptId/drafts.
 * A draft is a named line of revisions; exactly one draft is "current" and the
 * manuscript content is the latest revision of that draft.
 *
 * @typedef {{
 *   name: string,
 *   is_current: boolean,
 *   head: {id: string, message: string, created_at: string},
 *   revision_count: number
 * }} Draft
 */

import { apiFetchJson } from './http.js';

const base = (projectId, manuscriptId) =>
  `/api/projects/${projectId}/manuscripts/${manuscriptId}/drafts`;

async function request(url, options, fallback) {
  return apiFetchJson(url, options, fallback);
}

const json = (method, body) => ({
  method,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
});

/** @returns {Promise<Draft[]>} */
export function listDrafts(projectId, manuscriptId) {
  return request(base(projectId, manuscriptId), {}, 'Failed to load drafts.');
}

/** @returns {Promise<Draft>} */
export function getDraft(projectId, manuscriptId, name) {
  return request(`${base(projectId, manuscriptId)}/${encodeURIComponent(name)}`, {}, 'Draft not found.');
}

/**
 * Create a draft (copied from the main draft, or from `fromRevisionId`).
 * @returns {Promise<Draft>}
 */
export function createDraft(projectId, manuscriptId, name, fromRevisionId) {
  return request(
    base(projectId, manuscriptId),
    json('POST', fromRevisionId ? { name, from_revision_id: fromRevisionId } : { name }),
    'Failed to create draft.',
  );
}

/** @returns {Promise<Draft>} */
export function renameDraft(projectId, manuscriptId, name, newName) {
  return request(
    `${base(projectId, manuscriptId)}/${encodeURIComponent(name)}`,
    json('PATCH', { name: newName }),
    'Failed to rename draft.',
  );
}

/** @returns {Promise<void>} */
export function deleteDraft(projectId, manuscriptId, name) {
  return request(
    `${base(projectId, manuscriptId)}/${encodeURIComponent(name)}`,
    { method: 'DELETE' },
    'Failed to delete draft.',
  );
}

/**
 * Make a draft current. The manuscript content becomes the draft's latest revision.
 * @returns {Promise<Draft>}
 */
export function switchDraft(projectId, manuscriptId, name) {
  return request(
    `${base(projectId, manuscriptId)}/${encodeURIComponent(name)}/switch`,
    { method: 'POST' },
    'Failed to switch draft.',
  );
}
