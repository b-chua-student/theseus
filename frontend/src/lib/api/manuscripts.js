// Existing HTTP contracts. Callers retain response parsing and UI behavior.
export function listManuscripts() {
  return fetch('/api/documents');
}

export function getManuscript(id) {
  return fetch(`/api/documents/${id}`);
}

export function createManuscript(id) {
  return fetch('/api/documents', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ document_id: id }),
  });
}

export function saveManuscript(id, content) {
  return fetch('/api/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ document_id: id, content }),
  });
}

// TODO(API): Add revisions, drafts, merge, and indexing requests only after
// the backend defines their endpoints and response contracts.
