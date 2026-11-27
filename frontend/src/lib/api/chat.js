/**
 * Assistant (conversation) API client.
 *
 * Conversations are scoped under /api/projects/:projectId/conversations and
 * require an authenticated session cookie. Vite proxies /api/* to the Flask
 * backend at http://localhost:5000 during development.
 *
 * Two-step flow:
 *   1. startConversation(projectId)            -> conversation id
 *   2. askConversation(projectId, id, query)    -> { answer, citations }
 *
 * askConversation asks for a stream of newline-delimited JSON records so that the server can
 * report progress while an answer is being checked. It also accepts the plain JSON body:
 *   {"type":"status","message":...}              progress; never carries draft text
 *   {"type":"answer","answer":...,"citations":[...]}   terminal
 *   {"type":"error","error":...,"code":...,"status":...} terminal
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

const NDJSON = 'application/x-ndjson';

/** Normalize the terminal payload for both supported response formats. */
function terminalAnswer({ answer, citations, unverified_draft }) {
  const result = { answer, citations: citations ?? [] };
  if (typeof unverified_draft === 'string' && unverified_draft.trim()) {
    return { ...result, unverified_draft };
  }
  return result;
}

/** @param {string} message @param {{ code?: string, status?: number }} [details] */
function streamError(message, details = {}) {
  return Object.assign(new Error(message), { code: details.code ?? undefined, status: details.status ?? undefined });
}

/**
 * Read records from an NDJSON response until the terminal record arrives.
 * @param {Response} res
 * @param {(message: string) => void} [onStatus]
 * @returns {Promise<{ answer: string, unverified_draft?: string, citations: Array<object> }>}
 */
async function readStream(res, onStatus) {
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  const handle = (line) => {
    if (!line.trim()) return null;
    const record = JSON.parse(line);
    if (record.type === 'status') onStatus?.(record.message);
    if (record.type === 'answer') return terminalAnswer(record);
    if (record.type === 'error') throw streamError(record.error, record);
    return null;
  };

  for (;;) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });
    const lines = buffer.split('\n');
    buffer = lines.pop();
    for (const line of lines) {
      const result = handle(line);
      if (result) return result;
    }
    if (done) break;
  }
  const result = handle(buffer);
  if (result) return result;
  throw streamError('The assistant did not finish replying. Please try again.');
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
 * @param {{ web?: boolean, manuscript?: boolean }} checked  The checked Web and Manuscript items.
 * @param {{ onStatus?: (message: string) => void }} [options]
 * @returns {Promise<{ answer: string, unverified_draft?: string, citations: { key: string | number, source_id: string, title: string | null, location: string }[] }>}
 */
export async function askConversation(projectId, conversationId, query, contextScope = "source_library", sourceIds = null, manuscriptText = "", quote = null, checked = {}, options = {}) {
  const res = await apiFetch(
    `/api/projects/${projectId}/conversations/${conversationId}/exchanges`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: `${NDJSON}, application/json;q=0.9` },
      body: JSON.stringify({ query, context_scope: contextScope, source_ids: sourceIds, manuscript_text: manuscriptText, quote, ...checked }),
    },
    'The assistant did not reply. Please try again.',
  );
  if ((res.headers.get('Content-Type') || '').startsWith(NDJSON)) return readStream(res, options.onStatus);
  const body = await res.json();
  return terminalAnswer(body);
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
