/**
 * Projects API client.
 * All requests are sent to /api/projects, which Vite proxies to the Flask
 * backend at http://localhost:5000 during development.
 */

import { apiFetch } from './http.js';

/**
 * Fetch all projects owned by the currently authenticated user.
 * @returns {Promise<Array>}
 */
export async function listProjects() {
  const res = await apiFetch('/api/projects', { credentials: 'include' }, 'Failed to load projects.');
  return res.json();
}

/**
 * Create a new project. The server derives the owner from the active session.
 * @param {string} projectName
 * @returns {Promise<void>}
 */
export async function createProject(projectName) {
  await apiFetch('/api/projects', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_name: projectName }),
    credentials: 'include',
  }, 'Failed to create project.');
}

/**
 * Fetch a single project by ID.
 * @param {string} projectId
 * @returns {Promise<Object>}
 */
export async function getProject(projectId) {
  const res = await apiFetch(`/api/projects/${projectId}`, { credentials: 'include' }, 'Project not found.');
  return res.json();
}

/**
 * Delete a project by ID.
 * @param {string} projectId
 * @returns {Promise<void>}
 */
export async function deleteProject(projectId) {
  await apiFetch(`/api/projects/${projectId}`, {
    method: 'DELETE',
    credentials: 'include',
  }, 'Failed to delete project.');
}

/**
 * Rename a project.
 * @param {string} projectId
 * @param {string} newName
 * @returns {Promise<void>}
 */
export async function renameProject(projectId, newName) {
  await apiFetch(`/api/projects/${projectId}/name`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: newName }),
    credentials: 'include',
  }, 'Failed to rename project.');
}

/**
 * Set or replace the description of a project.
 * @param {string} projectId
 * @param {string} description
 * @returns {Promise<void>}
 */
export async function editProjectDescription(projectId, description) {
  await apiFetch(`/api/projects/${projectId}/description`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ description }),
    credentials: 'include',
  }, 'Failed to update description.');
}

/**
 * Clear the description of a project.
 * @param {string} projectId
 * @returns {Promise<void>}
 */
export async function removeProjectDescription(projectId) {
  await apiFetch(`/api/projects/${projectId}/description`, {
    method: 'DELETE',
    credentials: 'include',
  }, 'Failed to remove description.');
}

/**
 * Transfer ownership of a project to another member.
 * @param {string} projectId
 * @param {string} newOwnerId  UUID of the member to promote
 * @returns {Promise<void>}
 */
export async function transferProjectOwnership(projectId, newOwnerId) {
  await apiFetch(`/api/projects/${projectId}/owner`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ new_owner_id: newOwnerId }),
    credentials: 'include',
  }, 'Failed to transfer ownership.');
}
