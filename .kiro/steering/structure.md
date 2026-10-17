# Project Structure

```
theseus/
├── .github/workflows/main.yml     # CI: lint + build for frontend and backend (PRs only)
├── .pre-commit-config.yaml        # Hooks: mypy, ruff, ruff-format, commitizen, gitleaks
├── .gitignore                     # Ignores: node_modules, .venv, manifold/, backend/.env, caches
├── pyproject.toml                 # Ruff lint/format config (scoped to backend/)
├── package.json                   # Root npm scripts: dev, lint, lint:frontend, lint:backend
├── README.md                      # Setup, branching strategy, run instructions
│
├── backend/
│   ├── app.py                     # Flask entry point; all REST API routes defined here
│   ├── manifold.py                # Manifold class — Git VCS abstraction over Dulwich
│   ├── test_database.py           # ChromaDB in-memory client stub (2 lines; not a test file)
│   ├── requirements.txt           # Python dependencies (unpinned names only)
│   ├── .mypy.ini                  # Strict mypy config
│   ├── .env                       # Local secrets (gitignored; copy from .env.example)
│   ├── .env.example               # Template for all environment variables
│   └── Repository/                # Empty directory on disk (NOT the runtime repo store)
│                                  # ⚠ Runtime repos live in backend/manifold/<document_id>/
│
└── frontend/
    ├── src/
    │   ├── main.js                # Svelte mount point; mounts App into #app
    │   ├── App.svelte             # Root component; state-based routing (dashboard ↔ editor)
    │   ├── app.css                # Global styles
    │   ├── assets/                # Static assets (empty in scaffold)
    │   ├── lib/
    │   │   └── Counter.svelte     # ⚠ Vite scaffold leftover; not used anywhere
    │   └── components/
    │       ├── dashboard.svelte   # Document list table + "New Document" button
    │       └── editor.svelte      # TipTap editor, toolbar, Save, and AI chat sidebar
    ├── index.html                 # Vite HTML entry
    ├── vite.config.js             # Vite config; proxies /api → http://localhost:5000
    ├── svelte.config.js           # Empty Svelte config (default settings)
    ├── eslint.config.js           # ESLint: recommended + svelte plugin; no custom rules yet
    ├── jsconfig.json              # JS path resolution for editor tooling
    └── package.json               # Frontend deps: Svelte 5, TipTap 3, Vite 8, ESLint 10
```

## Module Responsibilities

### `backend/app.py`
All Flask route definitions. Thin handlers only — business logic belongs in `Manifold` or future service modules. Current routes:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/documents` | Returns metadata list from `Manifold.list_documents()` |
| `POST` | `/api/save` | Commits document HTML via `manifold.commit()` |
| `GET` | `/api/documents/<document_id>` | Returns document content from `manifold.get_document()` |
| `POST` | `/api/chat` | Proxies message to Gemini; returns `{"reply": str}` |
| ~~`POST`~~ | ~~`/api/documents`~~ | ⚠ **Missing** — frontend calls this to create a new document but no backend handler exists |

### `backend/manifold.py`
The `Manifold` class is the sole owner of all Git operations. It wraps Dulwich's low-level API and models git commands as methods. Rules:
- Must carry `# mypy: ignore-errors` at the top (Dulwich is untyped)
- Use `persistent=False` in unit tests to get an in-memory `MemoryRepo`
- Runtime storage: `manifold/<document_id>/` (bare repo, one per document)
- Many methods are **stubs** (`init`, `clone`, `rm`, `mv`, `reset`, `status`, `diff`, `show`, `ls_files`, `cat_file`, `branch`, `checkout`, `tag`, `merge`, `remote`, `fetch`, `pull`, `push`) — they return `None` and are placeholders for future implementation

Implemented methods: `__init__`, `commit`, `log`, `get_document`, `list_documents`

### `frontend/src/App.svelte`
Client-side router. Holds top-level state (`documents`, `selectedId`). Renders `Dashboard` when `selectedId` is `null`, `DocumentEditor` otherwise. Owns the `load()` and `create()` lifecycle functions.

### `frontend/src/components/dashboard.svelte`
Receives `documents` array and callback props (`onselect`, `oncreate`). Renders the document table and "+ New Document" button. Pure presentational — no direct fetch calls.

### `frontend/src/components/editor.svelte`
Manages TipTap editor lifecycle (`onMount`/`onDestroy`), toolbar state, save (`POST /api/save`), load (`GET /api/documents/<id>`), and AI chat (`POST /api/chat`). Sends `{ document_id, message, document }` to chat — `document` is the editor's plain text.

## Key Architectural Rules

1. **All API routes are prefixed `/api/`** and defined exclusively in `backend/app.py`.
2. **Dulwich imports live only in `manifold.py`**. No other file should import Dulwich directly.
3. **Frontend uses Svelte 5 runes only** — never `export let`, never `$:` reactive statements.
4. **No URL routing library** — `App.svelte` uses `$state(null)` for `selectedId` as the only routing mechanism.
5. **Vite proxies `/api` to port 5000** — do not hardcode backend URLs in frontend fetch calls.
6. **`test_database.py` is not a test file** — it is a module that instantiates a ChromaDB client; it is imported by `app.py` with `# noqa: F401`.

## Branching & Commit Conventions

- **GitHub Flow**: short-lived branches off `main`; `main` is protected, no direct pushes.
- Branch name patterns observed: `feat/<description>`, `feat/<issue-number>-<description>`, `fix/<description>`, `chore/<description>`
- Commits must follow **Conventional Commits** (enforced by commitizen pre-commit hook): `feat(scope): message`, `fix(scope): message`, `chore(scope): message`, `docs(scope): message`, `refactor(scope): message`, `ci(scope): message`, `style(scope): message`
