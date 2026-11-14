# Design — THES-188: HTML Sanitizer for Manuscript Bodies

**Jira:** THES-188  
**Traces to:** requirements.md (this directory)

---

## 1. Architecture context

The project follows a hexagonal / ports-and-adapters layout:

```
backend/
  api/           ← Flask routes + Pydantic schemas  (adapter layer)
  services/      ← application services             (use-case layer)
  domain/        ← aggregates, entities, value objects
  repositories/  ← port interfaces + fake impls
```

The write path for a section body today is:

```
POST/PATCH route
  → Pydantic schema validates request JSON
  → Application service calls Manuscript.add_section / Manuscript.edit_section
  → Body("raw html") stored as a value object
  → ManuscriptRepository.save(manuscript)
```

THES-188 inserts a sanitization + size-check step into this path **before** the body reaches
the domain model.

---

## 2. Sanitizer library

**[VERIFY IN REPO]** — No HTML sanitization library is currently present in
`backend/requirements.txt`. The file lists: `chromadb`, `flask`, `flask_limiter`,
`commitizen`, `pre-commit`, `mypy`, `chonkie`, `dulwich`, `pytest`.

A library must be chosen and pinned. The design is written against an abstract
`sanitize(html: str, allowed_tags: ..., allowed_attributes: ...) -> str` interface
so the exact library is a substitutable implementation detail. When the team
selects a library it must be recorded in `backend/requirements.txt` at a pinned
version (REQ-02).

**[ASSUMPTION]** — The team will evaluate lightweight Python allow-list sanitizers
(e.g. `bleach`, `nh3`, or similar) and record the decision before implementation
begins. This design does not select one.

---

## 3. Where sanitization lives

Sanitization is an **infrastructure / application concern**, not a domain rule.
The `Body` value object is a plain string wrapper with no validation today
(`backend/domain/manuscript/value_objects.py`). Putting the sanitizer there
would couple the domain to a third-party library, which conflicts with the
hexagonal architecture.

**Chosen location: application service layer.**

A new module [VERIFY IN REPO — confirm naming convention matches existing
`backend/services/manuscript/` files] will expose a sanitization helper that is
called by the create- and edit-section service paths before they pass the body
string into the domain. The helper is a plain function (or a small class with a
single `clean` method) so it can be unit-tested without a Flask context.

```
backend/services/manuscript/
  sanitize_body.py          ← NEW — sanitize + size-check logic (THES-188)
```

[VERIFY IN REPO] — Confirm that `backend/services/manuscript/` is the correct
home for cross-cutting helpers; there may be a `utils/` or `shared/` module that
fits better.

---

## 4. Size check

The size check (REQ-03) measures `len(raw_html)` in characters (not bytes) before
sanitization is called.

- Threshold: **500,000 characters** (from THES-188 ticket).
- If exceeded: raise a domain-neutral exception (e.g. `ValueError` with a clear
  message, or a custom exception type — [VERIFY IN REPO] whether a custom
  exceptions module exists). The route layer catches this and returns HTTP 400
  with `{"error": "..."}`, consistent with the existing error shape in
  `backend/api/routes/manuscript.py`.
- The check runs **before** sanitization so over-limit payloads do not waste time
  in the sanitizer.

---

## 5. Allowed-tag list

The allowed-tag list is **not decided** (REQ-04 open decision). The design
reserves a single named constant (e.g. `ALLOWED_TAGS`, `ALLOWED_ATTRIBUTES`) in
`sanitize_body.py`. When the list is agreed it is set there and nowhere else.

The list must be verified against the Tiptap extensions active in the frontend
[VERIFY IN REPO — `frontend/src/`] before it is finalized.

---

## 6. Call-site integration

The sanitize helper is called at the two write-path entry points inside the
application services that handle section bodies:

1. The service or aggregate method that processes `add_section` body arguments.
2. The service or aggregate method that processes `edit_section` body arguments.

[VERIFY IN REPO] — The current services in `backend/services/manuscript/`
(`create_manuscript.py`, `update_manuscript.py`) deal only with manuscript title,
not section bodies. Inspect which service or route is responsible for
`add_section` / `edit_section` calls (THES-88 likely introduced or will introduce
these). Confirm before writing any call sites.

---

## 7. API error response

When a body exceeds the 500,000-character limit the route must return:

```json
HTTP 400
{"error": "<descriptive message>"}
```

This matches the existing 400 response shape throughout
`backend/api/routes/manuscript.py`.

---

## 8. Testing approach

Tests are written with `pytest` (see `pyproject.toml: [tool.pytest.ini_options]`).
The test client and repository fixtures from `backend/tests/conftest.py` are
reused where needed.

Three scopes of test are required (tracing to THES-188 AC):

| Scope | File location (proposed) | Covers |
|---|---|---|
| Unit — sanitize helper | [VERIFY IN REPO] `backend/tests/services/manuscript/test_sanitize_body.py` | AC-01-1, AC-01-2, AC-01-3, AC-03-1, AC-03-2 |
| Integration — service layer | [VERIFY IN REPO] existing service test files or new file | AC-01-4, AC-03-4 |
| API — route layer | [VERIFY IN REPO] `backend/tests/api/test_<section_route>.py` | AC-03-2, AC-03-3 |

[VERIFY IN REPO] — The section-body write route does not yet exist in
`backend/api/routes/manuscript.py`. Confirm which route and test file will be
the target once THES-88 is merged.

---

## 9. Dependency on THES-88

THES-188 sanitizes the body **on write**. The write path for section bodies is
being established by THES-88. If THES-88 has not been merged, task T-02 (call-site
integration) is blocked on it.

---

## 10. What this design does not cover

- Sanitizing bodies already in the store (no migration, out of scope).
- Frontend validation.
- Title fields (plain text, no HTML).
- Attribute-level allow-listing specifics (depends on the library chosen and the
  agreed tag list from REQ-04).
