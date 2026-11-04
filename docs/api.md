# API Reference

Base path: `/api`. All requests and responses are JSON. Authentication is a cookie session.

## Conventions

**Authentication.** `POST /api/auth/login` or `/register` sets a session cookie. Every endpoint below
except those two (and `/logout`) requires it, otherwise the response is `401 {"error": "Unauthorized"}`.
Send requests with credentials, e.g. `curl -c jar -b jar`.

**IDs** are UUID strings. `{p}` = project id, `{m}` = manuscript id.

**Errors** have the shape `{"error": "message"}`, plus `"code"` for domain errors and `"details"`
(Pydantic validation errors) for `400 Invalid request`.

| Status | Meaning                                                       |
| ------ | ------------------------------------------------------------- |
| 400    | Invalid body, or a domain rule was violated                   |
| 401    | Not logged in, or bad credentials                             |
| 404    | Project, manuscript, source, conversation or history not found |
| 409    | Conflict (email taken, nothing to commit, pending chat answer) |
| 422    | Password too weak                                             |
| 429    | Rate limited (see below)                                      |
| 502/503| AI provider failed / not configured                           |

**Rate limits** (per IP): 100/day and 20/hour by default; `POST /auth/login` and `/auth/register`
are 5/minute. `GET /healthz` is exempt.

---

## Health

| Method | Path       | Response                |
| ------ | ---------- | ----------------------- |
| GET    | `/healthz` | `200 {"status": "ok"}`  |

## Auth

| Method | Path                | Body                                     | Success                                         |
| ------ | ------------------- | ---------------------------------------- | ----------------------------------------------- |
| POST   | `/api/auth/register`| `display_name`, `email`, `password`      | `201 {id, display_name}` (also logs in)        |
| POST   | `/api/auth/login`   | `email`, `password`                      | `200 {id, display_name}`                        |
| GET    | `/api/auth/me`      | -                                        | `200 {id, display_name, email}`                 |
| POST   | `/api/auth/logout`  | -                                        | `204`                                           |

Limits: `display_name`, `email`, `password` 1-128 characters. Errors: `401` bad credentials,
`409` email already registered, `422` weak password.

```bash
curl -c jar -H 'Content-Type: application/json' \
  -d '{"email":"a@example.com","password":"..."}' localhost:5000/api/auth/login
```

## Projects

| Method | Path                         | Body                       | Success                          |
| ------ | ---------------------------- | -------------------------- | -------------------------------- |
| GET    | `/api/projects`              | -                          | `200 [Project]` (yours)          |
| POST   | `/api/projects`              | `project_name` (1-50)      | `201`                            |
| GET    | `/api/projects/{p}`          | -                          | `200 ProjectDetail`              |
| DELETE | `/api/projects/{p}`          | -                          | `204`                            |
| PATCH  | `/api/projects/{p}/name`     | `name` (1-50)              | `204`                            |
| PUT    | `/api/projects/{p}/description` | `description` (non-empty) | `204`                          |
| DELETE | `/api/projects/{p}/description` | -                       | `204`                            |
| PATCH  | `/api/projects/{p}/owner`    | `new_owner_id`             | `204`                            |

```jsonc
// Project
{ "id": "...", "name": "...", "description": null,
  "members": [{ "id": "...", "display_name": "...", "role": "owner" }],
  "created_at": "2026-01-01T00:00:00+00:00" }

// ProjectDetail: same, plus "owner": {id, display_name, email}; members also include "email"
```

## Manuscripts

Base: `/api/projects/{p}/manuscripts`

| Method | Path                                  | Body                          | Success                     |
| ------ | ------------------------------------- | ----------------------------- | --------------------------- |
| GET    | ``                                    | -                             | `200 [{id, project_id, title}]` |
| POST   | ``                                    | `title` (1-256), `template?` (bool) | `201 {id}`            |
| GET    | `/{m}`                                | query `view=working` (optional) | `200 Manuscript`          |
| DELETE | `/{m}`                                | -                             | `204`                       |
| PATCH  | `/{m}/title`                          | `title` (1-256)               | `204`                       |
| POST   | `/{m}/sections`                       | `heading` (1-128), `parent_id?` | `201`                     |
| DELETE | `/{m}/sections/{section_id}`          | -                             | `204`                       |
| PATCH  | `/{m}/sections/{section_id}/heading`  | `heading` (1-128)             | `204`                       |
| PUT    | `/{m}/sections/{section_id}/body`     | `body` (string, HTML)         | `204`                       |

```jsonc
// Manuscript
{ "id": "...", "project_id": "...", "title": "...",
  "sections": [{ "id": "...", "parent_id": null, "heading": "...", "ordinal": 0, "body": "<p>...</p>" }] }
```

By default `sections` comes from the current draft's latest revision when history exists. Use
`?view=working` to get the working copy with uncommitted edits.

Saving a manuscript triggers re-indexing for the assistant.

## Revisions

Base: `/api/projects/{p}/manuscripts/{m}/revisions`

| Method | Path                 | Body                                       | Success                         |
| ------ | -------------------- | ------------------------------------------ | ------------------------------- |
| POST   | `/history`           | -                                          | `201` (starts history tracking) |
| POST   | ``                   | `message` (1-256), `branch?` (1-64)        | `201 {id, message, created_at, draft}` |
| GET    | ``                   | query `branch` (optional)                  | `200 [RevisionSummary]`         |
| GET    | `/{revision_id}`     | -                                          | `200 RevisionDetail`            |
| POST   | `/{revision_id}/restore` | `branch?` (1-64)                       | `200 RevisionSummary`           |

`409` on commit means there are no changes since the last revision.

```jsonc
// RevisionSummary
{ "id": "...", "message": "...", "created_at": "..." }
// RevisionDetail: summary plus "sections": [same shape as Manuscript sections]
```

## Drafts (branches)

Base: `/api/projects/{p}/manuscripts/{m}/drafts`

| Method | Path               | Body                                        | Success                |
| ------ | ------------------ | ------------------------------------------- | ---------------------- |
| POST   | ``                 | `name` (1-64), `from_revision_id?`          | `201 Draft`            |
| GET    | ``                 | -                                           | `200 [Draft]`          |
| GET    | `/{name}`          | -                                           | `200 Draft`            |
| PATCH  | `/{name}`          | `name` (1-64)                               | `200 Draft`            |
| DELETE | `/{name}`          | -                                           | `204`                  |
| POST   | `/{name}/switch`   | -                                           | `200 Draft`            |

```jsonc
// Draft
{ "name": "main", "is_current": true,
  "head": { "id": "...", "message": "...", "created_at": "..." }, "revision_count": 3 }
```

## Sources

The source library. Not scoped to a project in the URL.

| Method | Path                          | Body                                                    | Success          |
| ------ | ----------------------------- | ------------------------------------------------------- | ---------------- |
| GET    | `/api/sources`                | -                                                       | `200 [Source]`   |
| POST   | `/api/sources`                | `title` (1-256), `file_ref`, `project_id` (UUID), `authors?` ([string]), `year?` | `201 {id}` |
| GET    | `/api/sources/{source_id}`    | -                                                       | `200 Source`     |
| DELETE | `/api/sources/{source_id}`    | -                                                       | `204`            |
| PATCH  | `/api/sources/{source_id}/metadata` | `title` (1-256), `authors?`, `year?`              | `204`            |

```jsonc
// Source
{ "id": "...", "title": "...", "authors": ["A. Author"], "year": 2024, "file_ref": "..." }
```

## Assistant

| Method | Path                                                      | Body                | Success                       |
| ------ | --------------------------------------------------------- | ------------------- | ----------------------------- |
| POST   | `/api/projects/{p}/conversations`                         | -                   | `201 {id}`                    |
| POST   | `/api/projects/{p}/conversations/{conversation_id}/exchanges` | `query` (1-4000, not blank) | `201 {answer}`   |
| GET    | `/api/projects/{p}/manuscripts/{m}/indexing-status`       | -                   | `200 IndexingStatus`          |

```jsonc
// IndexingStatus
{ "status": "not_indexed", "chunk_count": 0, "searchable": false }
```

`status` is `not_indexed` until the manuscript has been saved and indexed; `searchable` tells you
whether chat can retrieve from it.

Chat errors: `404` unknown conversation, `409` previous question still being answered,
`429` AI provider busy (honour `Retry-After`), `502` provider error, `503` assistant not configured.

```bash
curl -b jar -X POST localhost:5000/api/projects/$P/conversations          # -> {"id": "<cid>"}
curl -b jar -H 'Content-Type: application/json' \
  -d '{"query":"Summarise my introduction"}' \
  localhost:5000/api/projects/$P/conversations/$CID/exchanges            # -> {"answer": "..."}
```
