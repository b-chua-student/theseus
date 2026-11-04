/**
 * Manuscripts API client.
 * All requests are scoped under /api/projects/:projectId/manuscripts.
 * Vite proxies /api/* to the Flask backend at http://localhost:5000 during development.
 */

import { apiFetch } from './http.js';

/**
 * Fetch all manuscripts for a project.
 * @param {string} projectId
 * @returns {Promise<Array<{id: string, project_id: string, title: string}>>}
 */
export async function listManuscripts(projectId) {
  const res = await apiFetch(`/api/projects/${projectId}/manuscripts`, {
    credentials: 'include',
  }, 'Failed to load manuscripts.');
  return res.json();
}

/**
 * Fetch a single manuscript by ID, including all sections.
 * @param {string} projectId
 * @param {string} manuscriptId
 * @param {{working?: boolean}} [options]  By default content is the current draft's latest
 *   revision. Pass `working: true` for the working copy (uncommitted edits), which is
 *   what section edits operate on — use it when saving.
 * @returns {Promise<{id: string, project_id: string, title: string, sections: Array}>}
 */
export async function getManuscript(projectId, manuscriptId, { working = false } = {}) {
  const query = working ? '?view=working' : '';
  const res = await apiFetch(`/api/projects/${projectId}/manuscripts/${manuscriptId}${query}`, {
    credentials: 'include',
  }, 'Manuscript not found.');
  return res.json();
}

/**
 * Create a new manuscript in a project.
 * @param {string} projectId
 * @param {string} title
 * @param {boolean} [template=false]  Pre-populate with thesis template sections.
 * @returns {Promise<{id: string}>}
 */
export async function createManuscript(projectId, title, template = false) {
  const res = await apiFetch(`/api/projects/${projectId}/manuscripts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, template }),
    credentials: 'include',
  }, 'Failed to create manuscript.');
  return res.json();
}

/**
 * Delete a manuscript.
 * @param {string} projectId
 * @param {string} manuscriptId
 * @returns {Promise<void>}
 */
export async function deleteManuscript(projectId, manuscriptId) {
  await apiFetch(`/api/projects/${projectId}/manuscripts/${manuscriptId}`, {
    method: 'DELETE',
    credentials: 'include',
  }, 'Failed to delete manuscript.');
}

/**
 * Rename a manuscript.
 * @param {string} projectId
 * @param {string} manuscriptId
 * @param {string} newTitle
 * @returns {Promise<void>}
 */
export async function renameManuscript(projectId, manuscriptId, newTitle) {
  await apiFetch(`/api/projects/${projectId}/manuscripts/${manuscriptId}/title`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: newTitle }),
    credentials: 'include',
  }, 'Failed to rename manuscript.');
}

/**
 * Append a section to a manuscript.
 * @param {string} projectId
 * @param {string} manuscriptId
 * @param {string} heading
 * @param {string|null} [parentId=null]
 * @returns {Promise<void>}
 */
export async function appendSection(projectId, manuscriptId, heading, parentId = null) {
  await apiFetch(`/api/projects/${projectId}/manuscripts/${manuscriptId}/sections`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ heading, parent_id: parentId }),
    credentials: 'include',
  }, 'Failed to append section.');
}

/**
 * Remove a section from a manuscript.
 * @param {string} projectId
 * @param {string} manuscriptId
 * @param {string} sectionId
 * @returns {Promise<void>}
 */
export async function removeSection(projectId, manuscriptId, sectionId) {
  await apiFetch(`/api/projects/${projectId}/manuscripts/${manuscriptId}/sections/${sectionId}`, { method: 'DELETE', credentials: 'include' }, 'Failed to remove section.');
}

/**
 * Rename a section's heading.
 * @param {string} projectId
 * @param {string} manuscriptId
 * @param {string} sectionId
 * @param {string} newHeading
 * @returns {Promise<void>}
 */
export async function renameSection(projectId, manuscriptId, sectionId, newHeading) {
  await apiFetch(`/api/projects/${projectId}/manuscripts/${manuscriptId}/sections/${sectionId}/heading`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ heading: newHeading }),
      credentials: 'include',
    }, 'Failed to rename section.');
}

/**
 * Replace the body of a section.
 * @param {string} projectId
 * @param {string} manuscriptId
 * @param {string} sectionId
 * @param {string} body
 * @returns {Promise<void>}
 */
export async function editSectionBody(projectId, manuscriptId, sectionId, body) {
  await apiFetch(`/api/projects/${projectId}/manuscripts/${manuscriptId}/sections/${sectionId}/body`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ body }),
      credentials: 'include',
    }, 'Failed to save section body.');
}
