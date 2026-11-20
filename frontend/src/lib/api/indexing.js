/**
 * Indexing status API client.
 * GET /api/projects/:projectId/manuscripts/:manuscriptId/indexing-status
 */

import { apiFetch } from './http.js';

/**
 * Fetch the indexing status of a manuscript's content in the assistant's index.
 * @param {string} projectId
 * @param {string} manuscriptId
 * @returns {Promise<{
 *   status: 'not_indexed' | 'pending' | 'indexing' | 'indexed' | 'failed',
 *   chunk_count: number,
 *   searchable: boolean
 * }>}
 */
export async function getIndexingStatus(projectId, manuscriptId) {
  const res = await apiFetch(`/api/projects/${projectId}/manuscripts/${manuscriptId}/indexing-status`, {
    credentials: 'include',
  }, 'Failed to load indexing status.');
  return res.json();
}
