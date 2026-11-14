# Tasks — THES-188: HTML Sanitizer for Manuscript Bodies

**Jira:** THES-188  
**Traces to:** requirements.md, design.md (this directory)

---

## Dependency graph

```
T-01 (repository discovery)
  └─► T-02 (choose & pin library)
        └─► T-03 (sanitize_body module)
              ├─► T-04 (call-site integration)
              │     └─► T-06 (API-layer tests)
              └─► T-05 (unit tests for sanitize_body)
```

T-04 is additionally blocked on **THES-88** (section-body write path) being
merged or at least branch-available.

---

## Dependency table

| Task | Depends on | Blocked by external |
|------|-----------|---------------------|
| T-01 | — | — |
| T-02 | T-01 | — |
| T-03 | T-02 | — |
| T-04 | T-03 | THES-88 (section-body write path) |
| T-05 | T-03 | — |
| T-06 | T-04 | THES-88 |

---

## Tasks

### T-01 — Repository discovery

**Requirement trace:** all requirements (prerequisite)  
**Status:** ⚠ Must be completed before any implementation task.

Steps:

1. Confirm which service(s) and route(s) own the section-body write path
   (expected to be introduced by THES-88). Record exact file paths and function
   names.
2. Inspect `frontend/src/` to identify which Tiptap extensions are active and
   what HTML tags they emit. Record this list as input to the REQ-04 decision.
3. Check whether a custom exceptions module exists (e.g. `backend/domain/exceptions.py`
   or similar). If it does, note the class to reuse for the size-limit error.
4. Confirm naming and location conventions for a new helper module under
   `backend/services/manuscript/` (or identify whether a shared `utils/` path
   is preferred).
5. Confirm the team's dependency-pinning strategy: exact versions in
   `backend/requirements.txt`, or a lock file (e.g. `pip-tools` `.txt` output).
6. Record findings in a brief discovery note (a comment on the THES-188 Jira
   ticket or a PR description is sufficient).

**Deliverable:** Written discovery note; no code changes.

---

### T-02 — Choose and pin the sanitizer library

**Requirement trace:** REQ-02  
**Depends on:** T-01

Steps:

1. Evaluate candidate lightweight allow-list sanitizers for Python 3.12.
   [ASSUMPTION — candidates include `bleach` and `nh3`; the team must make the
   final call. `bleach` is widely used but requires `html5lib`; `nh3` wraps
   Rust's `ammonia` and has minimal Python dependencies. Verify current
   maintenance status of both.]
2. Verify the chosen library has no dependency conflicts with the packages
   already in `backend/requirements.txt`.
3. Add the chosen library at an exact pinned version to `backend/requirements.txt`.
4. Record the rationale for the choice (comment on THES-188 or PR description).

**Deliverable:** One-line addition to `backend/requirements.txt`. No other files
changed.

---

### T-03 — Implement `sanitize_body` module

**Requirement trace:** REQ-01, REQ-02, REQ-03, REQ-04  
**Depends on:** T-02 (library pinned), T-01 (discovery of conventions and
exception type)  
**Blocked until:** REQ-04 allowed-tag list is agreed.

Steps:

1. Create [VERIFY IN REPO — exact path from T-01 discovery]
   `backend/services/manuscript/sanitize_body.py`.
2. Define `ALLOWED_TAGS` and `ALLOWED_ATTRIBUTES` constants reflecting the
   agreed allowed-tag list (REQ-04). These must be the single authoritative
   definitions (AC-04-1).
3. Implement a `sanitize_body(html: str) -> str` function (or equivalent) that:
   - Checks `len(html) > 500_000` first and raises an appropriate exception
     (AC-03-4). Use the exception type identified in T-01; default to
     `ValueError` if no custom type exists.
   - Passes the HTML through the chosen library with `ALLOWED_TAGS` and
     `ALLOWED_ATTRIBUTES` (AC-01-1 through AC-01-4).
   - Returns the cleaned string.
4. Add Google-style docstrings consistent with `pyproject.toml` ruff/pydocstyle
   settings.
5. Add type annotations (all parameters and return type) consistent with the
   existing codebase style.

**Deliverable:** `sanitize_body.py` module. No other application files changed.

---

### T-04 — Integrate sanitizer into the section-body write path

**Requirement trace:** REQ-01 (AC-01-4), REQ-03  
**Depends on:** T-03  
**External dependency:** THES-88 — section-body write service/route must exist.

Steps:

1. Identify the exact call sites from T-01 discovery (the service methods
   handling `add_section` body and `edit_section` body).
2. Import `sanitize_body` from the new module at each call site.
3. Call `sanitize_body(raw_body)` before the body string is passed to the domain
   model.
4. In the route layer, catch the size-limit exception raised by `sanitize_body`
   and return `{"error": "<message>"}` with HTTP 400 (AC-03-3), consistent with
   the existing error handling pattern in `backend/api/routes/manuscript.py`.
5. Confirm that no call site bypasses the sanitizer (all paths that write a body
   go through it).

**Deliverable:** Changes to the service(s) and route(s) identified in T-01.
Exact file paths are [VERIFY IN REPO].

---

### T-05 — Unit tests for `sanitize_body`

**Requirement trace:** REQ-01 (AC-01-1, AC-01-2, AC-01-3), REQ-03 (AC-03-1,
AC-03-2, AC-03-4)  
**Depends on:** T-03

Create [VERIFY IN REPO — confirm path convention]
`backend/tests/services/manuscript/test_sanitize_body.py`.

Required test cases (minimum; expand as the agreed tag list warrants):

| Test name (suggested) | What it asserts | Traces to |
|---|---|---|
| `test_script_tag_is_stripped` | `<script>alert(1)</script>` → output contains no `<script>` and no `alert(1)` | AC-01-1 |
| `test_script_content_is_stripped` | Inline script content does not appear in output | AC-01-1 |
| `test_allowed_formatting_is_kept` | At least one allowed tag (e.g. `<p>`, `<strong>`) survives after sanitization (blocked on REQ-04 decision — parameterize over agreed allowed tags) | AC-01-2 |
| `test_disallowed_tag_is_stripped_text_preserved` | A tag outside the allow-list is removed but its text content remains | AC-01-2 |
| `test_disallowed_attribute_is_removed` | `onclick` or `style` attribute on an allowed tag is stripped | AC-01-3 |
| `test_body_at_limit_is_accepted` | Input of exactly 500,000 characters returns without raising | AC-03-1 |
| `test_body_over_limit_raises` | Input of 500,001 characters raises the expected exception before sanitization | AC-03-2, AC-03-4 |
| `test_empty_body_is_accepted` | Empty string returns empty string (matches `Body` default in value object) | AC-01-4 |

Follow the fixture and naming conventions in
`backend/tests/services/manuscript/conftest.py` and existing test files.

**Deliverable:** `test_sanitize_body.py` with the cases above. No application
code changed.

---

### T-06 — API-layer tests for the size limit

**Requirement trace:** REQ-03 (AC-03-2, AC-03-3)  
**Depends on:** T-04  
**External dependency:** THES-88 route must exist.

Add test cases to [VERIFY IN REPO — the section-body route test file, expected
to be introduced by THES-88, e.g.
`backend/tests/api/test_<section>_route.py`]:

| Test name (suggested) | What it asserts | Traces to |
|---|---|---|
| `test_oversized_body_returns_400` | POST/PATCH with a body of 500,001 chars → HTTP 400 | AC-03-2 |
| `test_oversized_body_error_key_present` | Response JSON contains `"error"` key | AC-03-3 |
| `test_body_at_limit_returns_success` | POST/PATCH with a body of exactly 500,000 chars → 2xx | AC-03-1 |

Use the `client` fixture from `backend/tests/conftest.py`. The 500,000-character
string can be generated with `"a" * 500_001` in the test body.

**Deliverable:** Additional test cases in the existing route test file.
No application code changed.

---

## Notes

- No application code is written or modified as part of producing this spec.
- The allowed-tag list (REQ-04) is a team decision. T-03 and T-05's
  `test_allowed_formatting_is_kept` test cannot be completed until that decision
  is recorded.
- The merge-conflict markers visible in
  `backend/services/manuscript/update_manuscript.py` should be resolved before
  THES-188 implementation begins, but that is out of scope for this ticket.
