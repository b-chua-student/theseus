/**
 * Assistant (conversation) API client.
 *
 * Conversations are scoped under /api/projects/:projectId/conversations and
 * require an authenticated session cookie. Vite proxies /api/* to the Flask
 * backend at http://localhost:5000 during development.
 *
 * Two-step flow:
 *   1. startConversation(projectId)            -> conversation id
 *   2. askConversation(projectId, id, query)    -> answer text
 */

import { apiFetch } from './http.js';

/**
 * Start a new conversation for a project.
 * @param {string} projectId
 * @returns {Promise<string>} conversation id
 */
export async function startConversation(projectId) {
  const res = await apiFetch(
    `/api/projects/${projectId}/conversations`,
    { method: 'POST' },
    'Could not start a conversation. Please try again.',
  );
  return (await res.json()).id;
}

/**
 * Ask a question in an existing conversation.
 * Errors carry `status` and `code` so the UI can decide whether a retry makes sense.
 * @param {string} projectId
 * @param {string} conversationId
 * @param {string} query
 * @param {"none" | "manuscript" | "source_library"} contextScope
 * @param {string[] | null} sourceIds
 * @param {string} manuscriptText  Sent only when the manuscript is part of the context.
 * @param {string | null} quote  The exact quoted passage, kept apart from the question.
 * @returns {Promise<string>} answer text
 */
export async function askConversation(projectId, conversationId, query, contextScope = "source_library", sourceIds = null, manuscriptText = "", quote = null) {
  const res = await apiFetch(
    `/api/projects/${projectId}/conversations/${conversationId}/exchanges`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, context_scope: contextScope, source_ids: sourceIds, manuscript_text: manuscriptText, quote }),
    },
    'The assistant did not reply. Please try again.',
  );
  return (await res.json()).answer;
}

/**
 * List the IDs of the project's library sources the assistant can search.
 * @param {string} projectId
 * @returns {Promise<string[]>}
 */
export async function listIndexedSourceIds(projectId) {
  const res = await apiFetch(`/api/projects/${projectId}/indexed-sources`, {}, 'Could not load indexed sources.');
  return (await res.json()).source_ids;
}

export async function listConversations(projectId) {
  const res = await apiFetch(`/api/projects/${projectId}/conversations`, {}, 'Could not load conversations.');
  return res.json();
}

export async function getConversation(projectId, conversationId) {
  const res = await apiFetch(`/api/projects/${projectId}/conversations/${conversationId}`, {}, 'Could not open conversation.');
  return res.json();
}
