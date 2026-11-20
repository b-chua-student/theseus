# Repository Findings — Theseus

> Auto-generated codebase analysis. Read this before starting work; trust its contents.

## 1. Project Summary

Theseus is a web-based document editor with integrated Git-like version control and an AI research assistant for academic writers. Users organise manuscripts (nested sections) into projects, version work via revisions (commits) and drafts (branches), cite from a source library, and ask an AI-powered assistant questions about their manuscript. It ships as a single deployable: a Svelte 5 SPA and Flask API served from one origin.

Six bounded contexts are planned: **identity, project, manuscript, revision_history, src_lib, assistant**.

## 2. Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend language | Python 3.12 |
| Web framework | Flask 3.1 |
| Validation | Pydantic 2.14 (per steering; not yet pinned in requirements.txt) |
| Rate limiting | Flask-Limiter |
| Production server | Gunicorn (per steering; Dockerfile uses `flask run`) |
| Storage (prod) | MongoDB via pymongo (per steering; not yet in requirements.txt) |
| Storage (tests) | In-memory fake adapters |
| AI | Google Gemini (`google-genai`) |
| Vector store | ChromaDB |
| Git in Python | Dulwich |
| Text chunking | Chonkie |
| Frontend framework | Svelte 5 (runes: `$state`, `$effect`, `$props`) |
| Frontend build | Vite 8 |
| Rich text editor | Tiptap 3 (StarterKit, extension-list, extension-text-style) |
| Frontend lint | ESLint 10 |
| Container | Docker (`python:3.12-slim`, port 5000) |

## 3. Architecture (Hexagonal / Ports & Adapters)

Layering inside each bounded context — dependencies point inward:

```
api/            → Flask blueprint (routes.py), Pydantic request models, API errors
services/       → one use case per file, one class per operation
models/         → aggregates, entities, value objects, domain errors, events
infrastructure/
  ports/        → interfaces services depend on
  adapters/     → in-memory + MongoDB (+ Gemini/Chroma) implementations
```

- `bootstrap/` is the composition root: `build_container()` wires in-memory adapters (tests); `build_mongo_container()` swaps in MongoDB.
- Contexts communicate via the in-process event bus, never by importing each other's services.
- `shared/` holds cross-cutting helpers.

> **Note:** The `main` branch currently uses a `repositories/` package (top-level) rather than the `infrastructure/ports/` + `infrastructure/adapters/` layout described in the steering files. The steering files define the **target** architecture that the staging refactoring aims to achieve.

## 4. Current Branch State — Critical

- **Current branch:** `feat/prepare-staging-branch`
- **Head commit:** `8d07a8d feat: remove hard-coded dependencies`
- **All implementation source code has been intentionally removed** (2,005 lines deleted) while test files were added (749 insertions).
- The `main` branch retains the full implementation.
- **Tests will fail on the current branch** — they import from `api.app`, `domain.manuscript`, `services.manuscript`, `repositories.manuscript`, none of which exist in the working tree.
- This branch appears to be preparing for a major refactoring to align with the target architecture in the steering files.

### Files present on current branch (backend)

```
backend/
  run.py                    # entry point: from api.app import create_app
  requirements.txt
  .mypy.ini                 # strict mypy config
  .env / .env.example
  tests/
    conftest.py             # shared fixtures (app, client, limited_app, etc.)
    api/
      test_create_manuscript_route.py
      test_delete_manuscript_route.py
      test_get_all_manuscript_route.py
      test_update_manuscript_route.py
    services/manuscript/
      conftest.py
      test_create_manuscript_service.py
      test_delete_manuscript_service.py
      test_get_all_manuscript.py
      test_update_manuscript_service.py
```

### Files on `main` (removed on current branch)

```
backend/
  api/app.py                              # Flask app factory (create_app)
  api/extensions.py                       # Flask-Limiter instance
  api/routes/manuscript.py                # Manuscript blueprint
  api/schemas/manuscript_requests.py      # Pydantic request models
  api/schemas/manuscript_responses.py     # Pydantic response models
  domain/manuscript/aggregates.py         # Manuscript aggregate root (section tree)
  domain/manuscript/entities.py           # Section entity
  domain/manuscript/value_objects.py      # Body, Heading
  domain/manuscript/interface.py          # Repository interface
  domain/revision_history/aggregates.py
  domain/revision_history/entities.py
  domain/revision_history/exceptions.py
  domain/revision_history/interface.py
  domain/revision_history/value_objects.py
  repositories/manuscript/fake_manuscript_repository.py
  repositories/manuscript/manuscript_repository.py
  repositories/revision_history/fake_revision_history_repository.py
  repositories/revision_history/revision_history_repository.py
  services/manuscript/create_manuscript.py
  services/manuscript/delete_manuscript.py
  services/manuscript/get_all_manuscript.py
  services/manuscript/get_manuscript.py
  services/manuscript/update_manuscript.py
```

## 5. Domain Model — Manuscript (from `main`)

**Manuscript** (aggregate root): `id: UUID`, `project_id: UUID`, `title: str`

- Title cannot be empty/whitespace (raises `ValueError`).
- Contains a tree of **Section** entities, each with: `id`, `parent_id`, `heading` (Heading VO), `body` (Body VO), `ordinal` (position among siblings).
- Operations: `rename`, `add_section`, `get_section`, `edit_section`, `remove_section` (cascade-deletes descendants), `reorder_section`, `move_section` (with cycle detection).
- Ordinals are kept contiguous after add/remove/reorder/move.

## 6. Services (interfaces inferred from tests)

| Service | Method | Behavior |
|---------|--------|----------|
| `CreateManuscriptService` | `execute(project_id, title) → Manuscript` | Generates UUID, saves to repo. Raises `ValueError` on blank title. |
| `GetAllManuscriptService` | `execute() → list[Manuscript]` | Delegates to `repo.get_all()`. |
| `GetManuscriptService` | `execute(id) → Manuscript` | Exists on `main`; no test file on current branch. |
| `UpdateManuscriptService` | `execute(id, title) → Manuscript` | Fetches, renames, saves. Raises `ValueError` on unknown id or blank title. |
| `DeleteManuscriptService` | `execute(id) → None` | Raises `ValueError("Manuscript with ID {id} not found")` if missing. |

## 7. API Endpoints (inferred from tests)

| Method | Path | Body | Success | Error |
|--------|------|------|---------|-------|
| POST | `/api/manuscripts/create` | `{"title": str}` | 201 `{id, title}` | 400 (empty title) |
| GET | `/api/manuscripts` | — | 200 `[{...}]` | — |
| PATCH | `/api/manuscripts/{id}` | `{"title": str}` | 200 `{title}` | 400 (bad UUID, non-object, malformed JSON, missing/wrong-type title), 404 (unknown id) |
| DELETE | `/api/manuscripts/{id}` | — | 204 | 400 (bad UUID), 404 (not found) |

**Rate limits:** create = 5/min, update = 10/min, delete = 10/min. Returns 429 when exceeded.

## 8. Repository Interface (inferred from tests)

```
ManuscriptRepository (interface):
  save(manuscript) → None
  get_by_id(uuid) → Manuscript | None
  get_all() → list[Manuscript]
  exists(uuid) → bool
  delete(uuid) → None   # (inferred; not all methods directly tested)

FakeManuscriptRepository(seed: bool)  # in-memory; seed=True pre-populates
RevisionHistoryRepository (interface) + FakeRevisionHistoryRepository
```

## 9. Testing Conventions

- **Framework:** pytest with `--import-mode=importlib`; config in `pyproject.toml` and `backend/.mypy.ini`.
- **Property-based tests:** hypothesis.
- **No external dependencies:** tests run against in-memory fakes only (no MongoDB, no Gemini API key).
- **Fixtures** (in `tests/conftest.py`):
  - `manuscript_repo` — seeded in-memory repo.
  - `bare_manuscript_repo` — empty in-memory repo.
  - `app` / `client` — Flask app + test client with rate limiting **off**.
  - `limited_app` / `limited_client` — rate limiting **on** (in-memory storage, resets before/after).
- **Test structure mirrors source:** `tests/api/`, `tests/services/<context>/`, `tests/domain/<context>/`.
- **Naming:** files `test_*.py`, functions `test_*`.
- **What to mock:** nothing external — use fake/in-memory adapters and value-object builders. The delete-route 404 test uses `MagicMock` to replace `app.extensions["delete_manuscript_service"]`.

## 10. Frontend

- **Svelte 5 SPA** with runes (`$state`, `$effect`, `$props`, `$state.raw`).
- **Vite dev server** proxies `/api` → `http://localhost:5000` (Flask).
- **Components:**
  - `App.svelte` — root; toggles between dashboard and editor views.
  - `dashboard.svelte` — document list table (name, author, last modified, last commit).
  - `editor.svelte` — Tiptap editor with formatting toolbar (bold, italic, headings, lists, code, undo/redo), save button, and an AI chat sidebar.
- **Current frontend API calls:** `/api/documents` (GET list), `/api/documents/{id}` (GET content), `/api/save` (POST content), `/api/chat` (POST message + doc content).

> **Mismatch:** The frontend calls `/api/documents`, `/api/save`, `/api/chat` but the backend (on `main`) implements `/api/manuscripts/*`. The frontend and backend APIs are not yet aligned. The frontend appears to be from an earlier prototype.

## 11. CI/CD

- **Branching:** GitHub Flow — `main` is protected and always deployable. All work on short-lived branches (`feat/...`, `fix/...`, `chore/...`, `tests/...`). PRs required.
- **Commit format:** Commitizen — `feat(scope): message`, `fix(scope): message`, etc.
- **Pre-commit hooks:** mypy, ruff (lint + format), commitizen (commit-msg), gitleaks (secrets).
- **CI (`main.yml`):** runs on PRs — two parallel jobs:
  - Frontend: `npm ci`, `npm run lint`, `npm run build`.
  - Backend: `pip install -r requirements.txt`, `ruff check`, `ruff format --check`, `mypy`, `pytest`.
- **Staging (`staging.yaml`):** Docker build + container smoke test on `staging` branch.

## 12. Linting & Type Checking

- **ruff check:** `E, F, W, I, B, UP, SIM, A, T20, ANN, FBT, D` — Google docstring convention, 100-char line length, target py312.
  - Per-file ignores: `backend/domain/**` ignores `A002`; `backend/tests/**` ignores `D, ANN001`.
- **ruff format:** double quotes.
- **mypy:** strict (`disallow_any_explicit`, `disallow_any_decorated`, `disallow_any_unimported`, `warn_unreachable`, `extra_checks`). Error codes: `ignore-without-code`, `redundant-expr`, `truthy-bool`. `pretty` and `show_error_codes` enabled.
  - `ignore_missing_imports` for `dotenv.*` and `manifold.*`.

## 13. Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | ruff config (lint, format, per-file-ignores), mypy config, pytest config (`pythonpath=["backend"]`, `testpaths=["backend/tests"]`) |
| `backend/.mypy.ini` | strict mypy settings (overrides pyproject for backend) |
| `backend/requirements.txt` | `chromadb, flask, flask_limiter, commitizen, pre-commit, mypy, chonkie, dulwich, pytest` — **unpinned** |
| `backend/.env.example` | `GEMINI_API_KEY`, `SECRET_KEY`, `FLASK_APP`, `FLASK_DEBUG`, `HOST`, `PORT`, `CHROMA_PERSIST_PATH`, `GIT_REPO_DIR`, `CHUNK_SIZE` |
| `Dockerfile` | `python:3.12-slim`, installs from `requirements.txt`, serves via `flask --app application.app:create_app run --host=0.0.0.0 --port=5000` |
| `package.json` (root) | `concurrently` runs frontend (`vite`) + backend (`python backend/run.py`); lint/format/fix/test scripts |
| `frontend/package.json` | Svelte 5, Vite 8, Tiptap 3, ESLint |
| `.pre-commit-config.yaml` | mypy v2.4.0, ruff v0.17.1, commitizen v4.19.2, gitleaks v8.30.0 |

## 14. Known Issues & Discrepancies

1. **Implementation removed on current branch:** All `api/`, `domain/`, `services/`, `repositories/` source is gone. Tests import these packages and will fail with `ModuleNotFoundError` until implementation is restored/rebuilt.
2. **Dockerfile entry-point mismatch:** Dockerfile uses `flask --app application.app:create_app run` but `run.py` imports `from api.app import create_app`. There is no `application/` package. Docker build would fail at runtime.
3. **Frontend-backend API mismatch:** Frontend calls `/api/documents`, `/api/save`, `/api/chat`; backend implements `/api/manuscripts/*`. These are not yet connected.
4. **Architecture drift:** `main` uses `repositories/` as a flat top-level package. Steering files (`structure.md`) prescribe `infrastructure/ports/` and `infrastructure/adapters/` inside each domain context. The staging refactoring likely targets this restructure.
5. **Unpinned dependencies:** `requirements.txt` has no version pins despite the tech steering requiring pinned versions. `requirements-prod.txt` (referenced in steering) does not exist yet.
6. **Missing dependencies:** `pydantic`, `pymongo`, `gunicorn`, `google-genai` are referenced in steering/docs but not in `requirements.txt`.
7. **`manifold/` directory:** Gitignored; contains unrelated test data directories (`Thesis 3`, `document 1`, `feafaa`). Not part of the application.

## 15. Commands Cheat-Sheet

```bash
# Dev (both frontend + backend)
npm run dev

# Lint
npm run lint                         # both frontend + backend
npm run lint:frontend                # frontend only
npm run lint:backend                 # ruff check + mypy
ruff check backend/                   # backend lint only
ruff format backend/                  # format backend
ruff check --fix backend/             # autofix lint issues

# Type check
mypy backend/

# Test
pytest backend/
npm run test:backend

# Frontend only
npm --prefix frontend run dev
npm --prefix frontend run lint
npm --prefix frontend run build

# Docker
docker build -t theseus:staging .
docker run -p 5000:5000 theseus:staging
```
