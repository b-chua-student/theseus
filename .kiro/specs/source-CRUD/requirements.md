# Requirements: Source Library Text Upload

Refs: `text-upload-intake.md`, `source_library_text_upload.feature` (scenario tags in `[brackets]`).
Decisions marked **(D#)** are defined in `design.md`.

## Scope
Text sources only (paste/type, plain text). Out: file upload, rich text, collaboration, bulk ops, external integrations, auto-tagging, custom metadata, full version history.

## Functional

| ID | Requirement |
|----|-------------|
| R1 | **Create.** Authenticated user creates a text source with `title` (req, 1–200), `content` (req, 1–100,000 chars, UTF-8), `description` (opt, ≤1000), `tags` (opt, ≤10; trimmed, deduped, blanks dropped), `contentType` (`documentation`\|`notes`\|`code`\|`other`, default `other`). Result: version 1, active. `[@create]` |
| R2 | **Validation.** Violations → 400 with per-field errors; nothing persisted. Applies equally to create and update. `[@validation]` |
| R3 | **Read.** Get one text source by id incl. content. Missing, removed, or other-project → 404. `[@read]` |
| R4 | **List.** Paginated (default 20, max 100) text sources; filter by `contentType`, `tag`; sort by `updatedAt` (default, desc) or `title`. Items omit full content, include 200-char `snippet`. Removed excluded. `[@read @filter @sort]` |
| R5 | **Update.** Replace editable fields (R1 set). Every successful update: `version += 1`, `updatedAt` refreshed. Failed update changes nothing. `[@update @versioning]` |
| R6 | **Delete.** Soft delete (`removed_at` set); record retained. Removed items vanish from list, search, assistant grounding. `[@delete]` |
| R7 | **Search.** Query matches title, description, tags, content; combinable with R4 filters; scoped to caller's project; excludes removed. Empty result is valid (200, empty list). `[@search]` |
| R8 | **AuthN/Z.** All endpoints require login (401 otherwise). Access scoped by project; foreign resources → 404. `[@security @auth]` |
| R9 | **Abuse control.** Write endpoints rate limited (429 + `Retry-After`). Request body capped (D8). `[@rate-limit]` |
| R10 | **Content safety.** Content stored verbatim, never interpreted as HTML or query syntax. Injection-safe queries. `[@xss @injection]` |
| R11 | **Library integration.** Text sources appear in the existing source list (`kind=text`). Add/update/remove emit domain events so the assistant (re)indexes or drops them; content provider serves text content. `[@integration @grounding]` |
| R12 | **UI.** Form with metadata + content, live char counter, read-only preview, draft autosave; card list with search, filters, sort; edit; delete with confirm; WCAG-aligned, responsive. `[@ui @accessibility @responsive]` |

## Non-functional

| ID | Requirement |
|----|-------------|
| N1 | Create ≤ 2 s for 10 KB. `[@performance]` |
| N2 | Search ≤ 1 s at 1,000 docs/project. |
| N3 | Concurrent users isolated; no cross-user leakage. `[@concurrency]` |
| N4 | Backward compatible: existing file sources and API contracts unchanged, no data migration required. |
| N5 | Round-trip fidelity: stored text equals submitted text byte-for-byte (UTF-8). `[@storage]` |

## Resolved intake questions
Max length = 100,000 chars. Markdown: not in Phase 1 (plain text). Versioning: counter only. Dedup: none. Sharing/privacy: project-scoped only.
