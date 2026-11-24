---
inclusion: fileMatch
fileMatchPattern: "tests/**"
---

**Framework:** pytest with `--import-mode=importlib`; config in `backend/pytest.ini` and `pyproject.toml`. Property-based tests use `hypothesis`.

**Spec-driven tests:** Use the approved `gherkin.feature` to write executable tests before changing application code. Match each scenario to its `S-###` entry in `tasks.md` and assert the outcome described in the scenario. Follow the pre- and post-implementation checks in [workflow.md](workflow.md).

**Fixtures:** shared fixtures live in `backend/tests/conftest.py` — `app`/`client` (rate limiting off), `limited_app`/`limited_client` (rate limiting on), `user_payload`, `registered_user`. Add context-specific fixtures in the nearest `conftest.py`.

**Naming:** test files are `test_*.py`, test functions `test_*`. Tests mirror source paths: `domain/<context>/models` → `tests/domain/<context>/models/`, services → `tests/services/<context>/`.

**What to mock:** nothing external. Tests run against the in-memory container (no MongoDB, no Gemini API key). Use fake/in-memory adapters and value-object builders; do not patch HTTP or database calls. Disable rate limiting via the `app` fixture unless explicitly testing limits.
