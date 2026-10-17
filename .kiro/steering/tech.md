# Tech Stack

## Backend

- **Python 3.12** — required; set in `pyproject.toml` (`target-version = "py312"`), `backend/.mypy.ini` (`python_version = 3.12`), and CI
- **Flask** — REST API framework; all route handlers must return `tuple[Response, int]`
- **Dulwich** — pure-Python Git library; used only by `Manifold` to build blob/tree/commit objects directly without a working tree or git CLI
- **ChromaDB** — in-memory vector DB client (stub only; `test_database.py` instantiates it but no routes use it)
- **Chonkie** — text chunking (in requirements; not yet called from any code)
- **google-genai** (`google.genai`) — Google Generative AI SDK; Gemini called in `/api/chat`
- **python-dotenv** — loads `.env` at startup via `load_dotenv()`; see `.env.example` for all keys
- **mypy** — strict static type checker (`backend/.mypy.ini`)
- **pytest** — test runner (installed; no test files written yet beyond the ChromaDB stub)
- **commitizen** — Conventional Commits enforcement in pre-commit

## Frontend

- **Svelte 5** — SPA; uses runes API exclusively (`$state`, `$props`, `$effect`, `$state.raw`)
- **TipTap 3** — ProseMirror-based rich-text editor (`@tiptap/core`, `@tiptap/starter-kit`, `@tiptap/extension-list`, `@tiptap/extension-text-style`)
- **Vite 8** — build tool and dev server; proxies all `/api/*` requests to `http://localhost:5000` (see `vite.config.js`)
- **ESLint 10** with `eslint-plugin-svelte` — linting; config in `frontend/eslint.config.js`
- **svelte-check** — installed as devDependency but not wired to a script yet

## Root / Shared Tooling

- **concurrently** — runs Vite dev server (`npm --prefix frontend run dev`) and Flask (`python backend/app.py`) simultaneously
- **ruff** — Python linter and formatter (config in `pyproject.toml`); only scopes `backend/`
- **pre-commit** hooks (`.pre-commit-config.yaml`): mypy, ruff, ruff-format, commitizen (commit-msg), gitleaks

## Ruff Configuration (`pyproject.toml`)

```toml
[tool.ruff]
src = ["backend"]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E","F","W","I","B","UP","SIM","A","T20","ANN","FBT","D"]
ignore = ["D100","D104","D203","D213"]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.format]
quote-style = "double"
```

Key implications:
- Line length **100**, double quotes, Google docstrings
- `T20` bans `print()`; use logging instead
- `ANN` requires type annotations on all function arguments and return values
- `D` requires Google-style docstrings on all public methods/functions (modules and packages exempt via D100/D104)
- `FBT` bans boolean positional arguments; use keyword-only booleans (e.g. `*, flag: bool`)

## mypy Configuration (`backend/.mypy.ini`)

- `strict = True` plus `disallow_any_explicit`, `disallow_any_decorated`, `disallow_any_unimported`, `warn_unreachable`, `extra_checks`
- Error codes enabled: `ignore-without-code`, `redundant-expr`, `truthy-bool`
- `# mypy: ignore-errors` at file top is required for any module that directly uses Dulwich objects (they are untyped). `manifold.py` already has this.

## Environment Variables (`.env.example`)

| Variable | Used? | Notes |
|---|---|---|
| `GEMINI_API_KEY` | ✅ | Read via `os.getenv()` in `app.py` |
| `SECRET_KEY` | ❌ | Defined in example but not consumed |
| `FLASK_APP` | ✅ | Standard Flask env var |
| `FLASK_DEBUG` | ✅ | Read in `app.py` `__main__` block |
| `HOST` | ❌ | Defined but `app.run()` doesn't read it |
| `PORT` | ✅ | Read in `app.py` `__main__` block |
| `CHROMA_PERSIST_PATH` | ❌ | Defined but not consumed |
| `GIT_REPO_DIR` | ❌ | `Manifold.DEFAULT_STORAGE_DIR` is hardcoded to `"manifold"` |
| `CHUNK_SIZE` | ❌ | Defined but not consumed |

## Common Commands

### Setup
```powershell
# From repo root
npm install                         # installs root deps; postinstall installs frontend deps

cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell
pip install -r requirements.txt
pre-commit install --hook-type pre-commit --hook-type commit-msg
```

### Development (from repo root)
```powershell
# Activate backend venv first, then:
npm run dev      # starts Vite (frontend) + Flask (backend) concurrently
```

### Linting
```powershell
npm run lint              # both: ESLint (frontend) + ruff + mypy (backend)
npm run lint:frontend     # ESLint only
npm run lint:backend      # ruff check backend/ && mypy backend/

# Individual backend tools (from backend/):
ruff check .
ruff format .
mypy .
```

### Testing
```powershell
# From backend/ with venv active:
pytest
```

### Build / CI verification
```powershell
# Backend compile check (used in CI):
python -m compileall -q .

# Frontend production build:
npm --prefix frontend run build
```

## CI (`.github/workflows/main.yml`)

- Triggers on pull requests only
- Two parallel jobs: **Frontend** (Node 20: install → lint → build) and **Backend** (Python 3.12: install → `ruff check .` → `python -m compileall -q .`)
- `pytest` is **not** run in CI yet — only compile-check is performed
