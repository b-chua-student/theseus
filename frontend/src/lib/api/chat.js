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
 * @returns {Promise<string>} answer text
 */
export async function askConversation(projectId, conversationId, query) {
  const res = await apiFetch(
    `/api/projects/${projectId}/conversations/${conversationId}/exchanges`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    },
    'The assistant did not reply. Please try again.',
  );
  return (await res.json()).answer;
}
