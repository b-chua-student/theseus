# HTTP API reference

Send JSON requests with `Content-Type: application/json` unless the route expects a file upload. Sign in via `POST /api/auth/login` with `email` and `password` and retain the session cookie. Registration also takes `display_name` and starts a session. Protected routes return `401` without authentication. Malformed requests return `400` with an `error` message, and some routes include field details. Use identifiers returned by create or list calls. Project creation returns an empty HTTP 201 response. List projects to find the new ID.

In the table, **project** means `/api/projects/{project_id}` and **manuscript** means `/api/projects/{project_id}/manuscripts/{manuscript_id}`.

| Resource | Methods and paths | Main inputs or outputs |
| --- | --- | --- |
| Health | `GET /api/health` | Liveness status |
| Account | `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`, `POST /api/auth/logout` | Account details and cookie session |
| OAuth | `GET /api/auth/oauth/providers`, `GET /api/auth/oauth/{provider}/start`, `GET /api/auth/oauth/{provider}/callback`, `POST /api/auth/oauth/{provider}/link`, `PATCH /api/auth/me` | Provider discovery, sign-in, and linked account actions |
| Projects | `GET, POST /api/projects`, `GET, DELETE` **project** | Create with `project_name`; retrieve project and membership metadata |
| Project fields | `PATCH` **project**`/name`, `PUT, DELETE` **project**`/description`, `PATCH` **project**`/owner` | `name`, `description`, or `new_owner_id` |
| Manuscripts | `GET, POST` **project**`/manuscripts`, `GET, DELETE` **manuscript**, `PATCH` **manuscript**`/title` | `title` and optional creation flag `template`; details include sections |
| Sections | `POST` **manuscript**`/sections`, `DELETE .../sections/{section_id}`, `PATCH .../sections/{section_id}/heading`, `PUT .../sections/{section_id}/body` | `heading`, optional `parent_id`, or `body` |
| Revisions | `GET, POST` **manuscript**`/revisions`, `POST .../revisions/history`, `GET .../revisions/{revision_id}`, `POST .../revisions/{revision_id}/restore` | Initialize, save, read, or restore history |
| Drafts | `GET, POST` **manuscript**`/drafts`, `GET, PATCH, DELETE .../drafts/{name}`, `POST .../drafts/{name}/switch`, `POST .../drafts/{name}/merge` | Named draft branches |
| Sources | `GET, POST /api/sources`, `GET, DELETE /api/sources/{source_id}`, `PATCH /api/sources/{source_id}/metadata` | Source upload and metadata |
| Text sources | `GET, POST /api/sources/text`, `GET /api/sources/text/search`, `GET, PUT, DELETE /api/sources/text/{source_id}` | Text source CRUD and search |
| Conversations | `GET, POST` **project**`/conversations`, `GET .../conversations/{conversation_id}` | Conversation IDs and stored exchanges |
| Assistant exchange | `POST` **project**`/conversations/{conversation_id}/exchanges` | `query` plus optional context fields; sends JSON or streams NDJSON when requested in `Accept` |
| Indexing | `GET` **manuscript**`/indexing-status`, `GET` **project**`/indexed-sources` | Index state, searchable flag, or source IDs |

For a validation drill, send `{"project_name":""}` to `POST /api/projects` while authenticated. Expect HTTP 400 and a JSON error. See the [route registrations](../backend/bootstrap/app.py) and the [assistant request model](../backend/domain/assistant/api/requests.py).
