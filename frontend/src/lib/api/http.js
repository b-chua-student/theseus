/**
 * Shared fetch helper for API clients.
 *
 * Centralizes two things every client in lib/api/ was repeating:
 *  - turning a non-ok response into an Error with the server's message, code
 *    and status attached
 *  - turning a *failed* fetch (offline, DNS, CORS, server unreachable) into a
 *    readable message instead of leaking "Failed to fetch" / "NetworkError…"
 *
 * Call sites keep their own fallback message for the "server responded but
 * gave no error body" case, since that fallback is specific to the endpoint
 * (e.g. "Failed to load manuscripts." vs "Manuscript not found.").
 */

/**
 * @param {string} url
 * @param {RequestInit} [options]
 * @param {string} fallbackMessage  Used when the response is not ok but has no
 *   parseable `error` field.
 * @returns {Promise<Response>}
 */
export async function apiFetch(url, options, fallbackMessage) {
  let res;
  try {
    res = await fetch(url, { credentials: 'include', ...options });
  } catch {
    throw new Error('Could not reach the server. Check your connection and try again.');
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw Object.assign(new Error(body.error || fallbackMessage), {
      code: body.code,
      status: res.status,
    });
  }
  return res;
}

/**
 * Like {@link apiFetch}, but also parses the JSON body (or returns null for a
 * 204 No Content response).
 * @returns {Promise<any>}
 */
export async function apiFetchJson(url, options, fallbackMessage) {
  const res = await apiFetch(url, options, fallbackMessage);
  return res.status === 204 ? null : res.json();
}

/** Shorthand for a JSON request body with the standard headers. */
export function jsonBody(method, body) {
  return {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  };
}
