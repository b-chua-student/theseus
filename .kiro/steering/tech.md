---
inclusion: fileMatch
fileMatchPattern: "backend/**"
---

Backend: Python 3.12, Flask 3.1, Pydantic 2.14, Flask-Limiter, Gunicorn. Frontend: Svelte 5, Vite, Tiptap.
Storage: MongoDB (pymongo) in production; in-memory adapters in tests. AI: Google Gemini (`google-genai`).
Lint: `ruff check backend/` (E/F/W/I/B/UP/SIM/A/T20/ANN/FBT/D, google docstrings, 100-char lines). Format: `ruff format backend/`.
Type check: `mypy backend/` — strict (`disallow_any_*`, `warn_unreachable`). Test: `pytest backend/`.
Use pinned runtime dependencies from `backend/requirements.txt`. Install `backend/requirements-dev.txt` for local development and CI; it includes the runtime requirements.
Prefer in-memory adapters for tests — never require a live MongoDB or Gemini API key.
Use `hypothesis` for property-based domain model tests.
Avoid adding heavy or unpinned dependencies.
Frontend lint: `npm run lint:frontend` (run from repo root).
