/**
 * Source Library API client.
 * All requests are sent to /api/sources, which Vite proxies to the Flask
 * backend at http://localhost:5000 during development.
 */

import { apiFetch } from './http.js';

/**
 * @typedef {{ id: string, title: string, authors: string[], year: number|null, file_ref: string }} Source
 */

/**
 * Fetch all active sources.
 * @returns {Promise<Source[]>}
 */
export async function listSources() {
  const res = await apiFetch('/api/sources', { credentials: 'include' }, 'Failed to load sources.');
  return res.json();
}

/**
 * Add a new source to the library.
 * @param {string} title
 * @param {string[]} authors
 * @param {number|null} year
 * @param {string} fileRef
 * @returns {Promise<{ id: string }>}
 */
export async function addSource(title, authors, year, fileRef) {
  const res = await apiFetch('/api/sources', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, authors, year: year || null, file_ref: fileRef }),
    credentials: 'include',
  }, 'Failed to add source.');
  return res.json();
}

/**
 * Fetch a single source by ID.
 * @param {string} sourceId
 * @returns {Promise<Source>}
 */
export async function getSource(sourceId) {
  const res = await apiFetch(`/api/sources/${sourceId}`, { credentials: 'include' }, 'Source not found.');
  return res.json();
}

/**
 * Remove (soft-delete) a source by ID.
 * @param {string} sourceId
 * @returns {Promise<void>}
 */
export async function removeSource(sourceId) {
  await apiFetch(`/api/sources/${sourceId}`, {
    method: 'DELETE',
    credentials: 'include',
  }, 'Failed to remove source.');
}

/**
 * Update the metadata (title, authors, year) of an existing source.
 * @param {string} sourceId
 * @param {string} title
 * @param {string[]} authors
 * @param {number|null} year
 * @returns {Promise<void>}
 */
export async function updateSourceMetadata(sourceId, title, authors, year) {
  await apiFetch(`/api/sources/${sourceId}/metadata`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, authors, year: year || null }),
    credentials: 'include',
  }, 'Failed to update source.');
}
