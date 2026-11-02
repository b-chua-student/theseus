// Return the Response so ChatPanel retains its existing reply/error handling.
export function sendChatMessage(id, message, document) {
  return fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ document_id: id, message, document }),
  });
}

// TODO(API): Context switching and source IDs need a backend contract.
// Keep the existing manuscript-only payload until those integrations exist.
