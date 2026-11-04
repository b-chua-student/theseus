/**
 * Revision history API client.
 * All requests are scoped under
 * /api/projects/:projectId/manuscripts/:manuscriptId/revisions.
 * Vite proxies /api/* to the Flask backend at http://localhost:5000 during development.
 */

import { apiFetch } from './http.js';

/**
 * Start revision history tracking for a manuscript.
 * @param {string} projectId
 * @param {string} manuscriptId
 * @returns {Promise<void>}
 */
export async function startRevisionHistory(projectId, manuscriptId) {
  await apiFetch(`/api/projects/${projectId}/manuscripts/${manuscriptId}/revisions/history`, {
    method: 'POST',
    credentials: 'include',
  }, 'Failed to start revision history.');
}

/**
 * Commit a snapshot of the manuscript as a new revision.
 * @param {string} projectId
 * @param {string} manuscriptId
 * @param {string} message  Commit message (1–256 chars).
 * @param {string} [branch]  Draft name (1–64 chars). Defaults to the current draft.
 * @returns {Promise<{id: string, message: string, created_at: string, draft: string}>}
 *   Rejects with an error whose `code` is 'revision.no_changes' when nothing changed.
 */
export async function commitRevision(projectId, manuscriptId, message, branch) {
  const res = await apiFetch(`/api/projects/${projectId}/manuscripts/${manuscriptId}/revisions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(branch ? { message, branch } : { message }),
    credentials: 'include',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw Object.assign(new Error(err.error || 'Failed to commit revision.'), { code: err.code });
  }
  return res.json();
}

/**
 * List all revisions for a manuscript on the given branch.
 * @param {string} projectId
 * @param {string} manuscriptId
 * @param {string} [branch]  Defaults to the current draft.
 * @returns {Promise<Array<{id: string, message: string, created_at: string}>>}
 */
export async function listRevisions(projectId, manuscriptId, branch) {
  const query = branch ? `?branch=${encodeURIComponent(branch)}` : '';
  const res = await apiFetch(
    `/api/projects/${projectId}/manuscripts/${manuscriptId}/revisions${query}`,
    undefined,
    'Failed to load revisions.',
  );
  return res.json();
}

/**
 * Fetch a single revision with its full section snapshot.
 * @param {string} projectId
 * @param {string} manuscriptId
 * @param {string} revisionId
 * @returns {Promise<{
 *   id: string,
 *   message: string,
 *   created_at: string,
 *   sections: Array<{id: string, parent_id: string|null, heading: string, ordinal: number, body: string}>
 * }>}
 */
export async function getRevision(projectId, manuscriptId, revisionId) {
  const res = await apiFetch(`/api/projects/${projectId}/manuscripts/${manuscriptId}/revisions/${revisionId}`, { credentials: 'include' }, 'Revision not found.');
  return res.json();
}

/**
 * Restore a manuscript to a previous revision.
 * The backend applies the revision's section snapshot to the manuscript
 * and records a new revision capturing the restore.
 * @param {string} projectId
 * @param {string} manuscriptId
 * @param {string} revisionId
 * @param {string} [branch]  Defaults to the current draft.
 * @returns {Promise<{id: string, message: string, created_at: string}>}
 */
export async function restoreRevision(projectId, manuscriptId, revisionId, branch) {
  const res = await apiFetch(`/api/projects/${projectId}/manuscripts/${manuscriptId}/revisions/${revisionId}/restore`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(branch ? { branch } : {}),
    credentials: 'include',
  }, 'Failed to restore revision.');
  return res.json();
}
