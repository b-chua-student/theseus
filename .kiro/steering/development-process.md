# Development Process

## Spec-Driven Development

When implementing a new feature or fixing a non-trivial bug, follow this sequence:

1. **Spec first** — write a short spec (requirements → design → task list) before touching source code
2. **Human approval** — present the spec and wait for explicit confirmation before starting implementation
3. **One task at a time** — implement tasks sequentially; do not start the next task until the current one passes linting and (where applicable) tests
4. **No scope creep** — implement only what the approved spec describes; raise a new spec for anything additional

## Human Approval Gates

The following actions require explicit user confirmation before proceeding:

- Any change to `backend/app.py` route signatures or response shapes (frontend compatibility)
- Any change to `Manifold` method signatures (callers in `app.py` depend on them)
- Adding new Python dependencies to `requirements.txt`
- Adding new npm dependencies to `frontend/package.json`
- Deleting or renaming existing files
- Changes to `.pre-commit-config.yaml` or `pyproject.toml` lint config
- Any schema or data-format change to the per-document Git repos in `manifold/`

## Multi-Agent Coordination

When parallel agents are working on this repo:

- **Backend agent** owns: `backend/app.py`, `backend/manifold.py`, `backend/requirements.txt`, `backend/.mypy.ini`, `pyproject.toml`
- **Frontend agent** owns: `frontend/src/`, `frontend/package.json`, `frontend/eslint.config.js`, `frontend/vite.config.js`
- **Shared files** (`.pre-commit-config.yaml`, `package.json`, `.gitignore`, `.github/workflows/main.yml`) require coordination — do not edit simultaneously

API contract changes (route paths, request/response JSON shapes) must be agreed on before either agent implements them, as both sides depend on the contract.

## Working with Gaps and Stubs

Several `Manifold` methods are stubs that return `None`:
`init`, `clone`, `rm`, `mv`, `reset`, `status`, `diff`, `show`, `ls_files`, `cat_file`, `branch`, `checkout`, `tag`, `merge`, `remote`, `fetch`, `pull`, `push`

Before implementing any stub, confirm the intended behavior and API contract with the user. The method signatures may need to change from `-> None`.

## Before Submitting a Change

- [ ] `npm run lint` passes with no errors (runs ruff + mypy + ESLint)
- [ ] `python -m compileall -q backend/` passes
- [ ] `npm --prefix frontend run build` passes (if frontend was touched)
- [ ] No secrets in committed files (gitleaks will block the commit)
- [ ] Commit message follows Conventional Commits format
- [ ] Branch is off `main` and named with correct prefix

## Things That Are NOT in CI Yet (but should be)

- `pytest` — test suite exists as infrastructure but is not run
- `mypy` — run locally and in pre-commit but not as a CI job
- `svelte-check` — installed as devDependency but not in a script or CI step
