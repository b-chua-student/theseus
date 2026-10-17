# Product: Theseus

Theseus is a web-based document editor with integrated Git-like version control and AI chat capabilities.

## Core Features

- **Document dashboard** — lists all saved documents with metadata (last commit hash, author, last-modified timestamp).
- **Rich-text editing** — TipTap editor with standard formatting (bold, italic, headings, lists, code blocks, undo/redo).
- **Git-backed versioning** — each document's HTML content is committed into its own bare Git repository on disk via the `Manifold` class (backed by Dulwich). Every save is a commit.
- **AI chat sidebar** — users can converse with a Gemini AI assistant while editing a document. The editor sends the document's plain text alongside the user's message (field `document`), but the current backend does not yet use that context.
- **Vector search (planned)** — ChromaDB and Chonkie are present in `requirements.txt` and `test_database.py` but are not yet wired to any API route or indexing pipeline.

## Known Gaps / Stubs (⚠ requires confirmation before implementing)

| Gap | Location | Notes |
|---|---|---|
| `POST /api/documents` route missing | `backend/app.py` | Frontend calls it in `App.svelte create()` to create a new document; backend has no handler |
| Commit author hardcoded | `app.py:save_document` | Always `"sample user / sampleuser@email.com"` — no auth layer exists |
| Commit message hardcoded | `app.py:save_document` | Always `"first commit"` for every save |
| Commit timezone hardcoded | `manifold.py:commit` | Always `"-0200"` regardless of user locale |
| `document` context ignored in AI chat | `app.py:test_ai_call` | Frontend sends `document_id` and `document` but backend only reads `message` |
| `GIT_REPO_DIR` env var unused | `.env.example` | `Manifold.DEFAULT_STORAGE_DIR` is hardcoded to `"manifold"`, not read from env |
| `SECRET_KEY`, `CHROMA_PERSIST_PATH`, `CHUNK_SIZE` env vars unused | `.env.example` | Defined but not consumed by any Python code |
| Gemini model hardcoded | `app.py:test_ai_call` | `"gemini-3.8-flash"` not configurable via env |

## Target Users

Developers and knowledge workers who want document editing with first-class version history and AI assistance.
