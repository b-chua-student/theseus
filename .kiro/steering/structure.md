---
inclusion: fileMatch
fileMatchPattern: "backend/**"
---

Hexagonal/ports-and-adapters design: one package per bounded context under `backend/domain/<context>/` (identity, project, manuscript, revision_history, src_lib, assistant); `shared/` holds cross-cutting helpers.
Layering inside a context — dependencies point inward:
- `api/` — Flask blueprint (`routes.py`), Pydantic request models (`requests.py`), API errors (`errors.py`).
- `services/` — one use case per file, one class per operation (e.g. `create_manuscript.py`).
- `models/` — aggregates, entities, value objects, domain errors, events.
- `infrastructure/ports/` — interfaces services depend on; `infrastructure/adapters/` — in-memory and MongoDB (and Gemini/Chroma) implementations.
`bootstrap/` is the composition root: `build_container()` wires in-memory adapters (tests); `build_mongo_container()` swaps in MongoDB.
Contexts communicate via the in-process event bus, never by importing each other's services.
`frontend/src/` — pages, components, `lib/api` client. `docs/` — setup, architecture, API reference.
Tests mirror source paths under `backend/tests/`: `tests/domain/<context>/`, `tests/services/<context>/`, `tests/api/`.
Test files are `test_*.py`; shared fixtures live in `conftest.py`.
