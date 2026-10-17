# Code Conventions & Quality Standards

## Python Style (enforced by ruff + mypy)

- **Line length**: 100 characters
- **Quotes**: double quotes
- **Imports**: sorted by ruff (isort rules via `I`); standard library → third-party → first-party (`backend/`)
- **Docstrings**: Google style on all public classes and methods; modules and packages are exempt (D100/D104 ignored)
- **Type annotations**: required on all function parameters and return types (`ANN` rules)
- **No `print()`**: use `logging` instead (`T20` rule)
- **No boolean positional args**: use keyword-only booleans (`FBT` rule) — e.g. `def foo(*, flag: bool)`
- **No builtin shadowing**: do not name variables `id`, `type`, `list`, `dict`, etc. (`A` rule)

## Python Type Safety

- mypy runs in strict mode; do not suppress errors with bare `# type: ignore` — always include the error code: `# type: ignore[assignment]`
- Files that import Dulwich objects directly must carry `# mypy: ignore-errors` at the very top (Dulwich has no type stubs)
- `disallow_any_explicit` means avoid `Any` in type annotations; use `object` or a proper generic instead
- `disallow_any_decorated` means decorated functions must still have typed signatures

## Flask Route Conventions

- Every route handler returns `tuple[Response, int]`
- Validate all incoming JSON fields with `isinstance()` before use; return `400` for invalid payloads
- Use `request.get_json()` (not `request.json`) to avoid exceptions on missing content-type
- Route functions must have Google-style docstrings

## Frontend Style

- Use **Svelte 5 runes API** exclusively:
  - State: `$state()`, `$state.raw()`
  - Props: `$props()`
  - Side effects: `$effect()`
  - Never use `export let`, `$:`, or `writable()` stores
- Component filenames: lowercase with hyphens if multi-word (current: `dashboard.svelte`, `editor.svelte`)
- Fetch calls are made from `App.svelte` (orchestration) or `editor.svelte` (document-specific); `dashboard.svelte` is purely presentational
- No URL hardcoding — all API calls use relative paths (`/api/...`); Vite proxies them to Flask

## Testing

- **No test suite exists yet** — `pytest` is installed and `test_database.py` is a stub, not a test file
- New backend logic should be unit-tested; use `Manifold(persistent=False)` to get an in-memory repo (no disk I/O)
- Test files belong in `backend/tests/` (directory is gitignored for `__pycache__` but tracked for `.py` files, per early commit history)
- **CI does not run pytest** — only `ruff check` and `python -m compileall` run in CI

## Commit & Branch Rules

- Conventional Commits enforced by commitizen pre-commit hook (stage: `commit-msg`)
- Format: `type(scope): subject` — e.g. `feat(manifold): add branch support`
- Scopes observed in history: file/module names (`app.py`, `manifold.py`, `editor.svelte`) or feature areas (`backend`, `frontend`)
- gitleaks runs on every commit — do not commit real API keys or secrets; use `.env` (gitignored)
- Branch name convention: `feat/<description>`, `fix/<description>`, `chore/<description>`

## What Belongs Where

| Concern | Location |
|---|---|
| API route definitions | `backend/app.py` only |
| Git/VCS logic | `backend/manifold.py` (`Manifold` class) only |
| Dulwich imports | `backend/manifold.py` only |
| ChromaDB/vector logic | `backend/test_database.py` (expand here or new module) |
| Frontend routing state | `frontend/src/App.svelte` |
| Reusable UI components | `frontend/src/components/` |
| Shared utilities | `frontend/src/lib/` (currently has unused scaffold; clean up before adding real utilities) |
