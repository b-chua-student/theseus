/**
 * Projects API client.
 * All requests are sent to /api/projects, which Vite proxies to the Flask
 * backend at http://localhost:5000 during development.
 */

/**
 * Fetch all projects owned by the currently authenticated user.
 * @returns {Promise<Array>}
 */
export async function listProjects() {
  const res = await fetch('/api/projects', { credentials: 'include' });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || 'Failed to load projects.');
  }
  return res.json();
}

/**
 * Create a new project. The server derives the owner from the active session.
 * @param {string} projectName
 * @returns {Promise<void>}
 */
export async function createProject(projectName) {
  const res = await fetch('/api/projects', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_name: projectName }),
    credentials: 'include',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || 'Failed to create project.');
  }
}

/**
 * Fetch a single project by ID.
 * @param {string} projectId
 * @returns {Promise<Object>}
 */
export async function getProject(projectId) {
  const res = await fetch(`/api/projects/${projectId}`, { credentials: 'include' });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || 'Project not found.');
  }
  return res.json();
}

/**
 * Delete a project by ID.
 * @param {string} projectId
 * @returns {Promise<void>}
 */
export async function deleteProject(projectId) {
  const res = await fetch(`/api/projects/${projectId}`, {
    method: 'DELETE',
    credentials: 'include',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || 'Failed to delete project.');
  }
}

/**
 * Rename a project.
 * @param {string} projectId
 * @param {string} newName
 * @returns {Promise<void>}
 */
export async function renameProject(projectId, newName) {
  const res = await fetch(`/api/projects/${projectId}/name`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: newName }),
    credentials: 'include',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || 'Failed to rename project.');
  }
}

/**
 * Set or replace the description of a project.
 * @param {string} projectId
 * @param {string} description
 * @returns {Promise<void>}
 */
export async function editProjectDescription(projectId, description) {
  const res = await fetch(`/api/projects/${projectId}/description`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ description }),
    credentials: 'include',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || 'Failed to update description.');
  }
}

/**
 * Clear the description of a project.
 * @param {string} projectId
 * @returns {Promise<void>}
 */
export async function removeProjectDescription(projectId) {
  const res = await fetch(`/api/projects/${projectId}/description`, {
    method: 'DELETE',
    credentials: 'include',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || 'Failed to remove description.');
  }
}

/**
 * Transfer ownership of a project to another member.
 * @param {string} projectId
 * @param {string} newOwnerId  UUID of the member to promote
 * @returns {Promise<void>}
 */
export async function transferProjectOwnership(projectId, newOwnerId) {
  const res = await fetch(`/api/projects/${projectId}/owner`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ new_owner_id: newOwnerId }),
    credentials: 'include',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || 'Failed to transfer ownership.');
  }
}
