# Requirements — THES-188: HTML Sanitizer for Manuscript Bodies

**Jira:** THES-188  
**Source:** Spec review 2026-11-08, item M-5  
**Status:** Needs decision (allowed-tag list unresolved — see REQ-04)  
**Parent ticket:** THES-88 (manuscript body write path)

---

## Background

Manuscript section bodies are stored as HTML produced by the Tiptap rich-text editor on the
frontend. At the time of writing, the `Body` value object (`backend/domain/manuscript/value_objects.py`)
accepts any string without inspection. THES-88 established the write path; THES-188 adds safety
to it by sanitizing that HTML before it is persisted and by rejecting bodies that exceed a
hard size limit.

---

## Requirements

### REQ-01 — Allow-list HTML sanitization on write

**EARS:** When a manuscript section body is written (created or updated), the system shall pass
the HTML through an allow-list sanitizer before persisting it, so that only permitted tags and
attributes survive.

**Acceptance criteria:**

- AC-01-1: Script tags (and their content) are stripped from the sanitized output.
- AC-01-2: Tags outside the agreed allow-list are stripped; their text content is preserved
  unless the tag is in a category that must be dropped entirely (e.g., `<script>`, `<style>`).
- AC-01-3: Attributes not on the allow-list for a given tag are removed.
- AC-01-4: The sanitized value, not the raw value, is what gets stored.

**Open issue:** The specific allowed-tag list has not been agreed. See REQ-04.

---

### REQ-02 — Sanitizer library must be verified in the repository

**EARS:** When the sanitizer library is added to the project, the system shall record it in the
pinned dependency file (`backend/requirements.txt`) at an exact version, so that the dependency
is reproducible and auditable.

**Acceptance criteria:**

- AC-02-1: The library appears in `backend/requirements.txt` [VERIFY IN REPO — confirm the
  team pins exact versions or uses a lock file strategy].
- AC-02-2: No transitive dependency is introduced that conflicts with the existing packages in
  `backend/requirements.txt`.
- AC-02-3: The library is lightweight; it must not pull in a full HTML rendering engine or
  browser runtime as a dependency. [ASSUMPTION — "avoid heavy dependencies" from project brief.]

---

### REQ-03 — Hard size limit on manuscript body

**EARS:** When a manuscript section body write is attempted, the system shall reject bodies
longer than 500,000 characters with HTTP 400 before sanitization runs.

**Acceptance criteria:**

- AC-03-1: A body of exactly 500,000 characters is accepted.
- AC-03-2: A body of 500,001 or more characters is rejected with HTTP 400.
- AC-03-3: The rejection response includes an `"error"` key in its JSON body, consistent with
  other 400 responses in the API (see `backend/api/routes/manuscript.py`).
- AC-03-4: Sanitization is not invoked for over-limit bodies (size check runs first).

---

### REQ-04 — Allowed HTML tag list (open decision)

**EARS:** When the allowed-tag list is agreed, the system shall encode it as the single
authoritative configuration passed to the sanitizer, so that every write path uses the same set.

**Acceptance criteria:**

- AC-04-1: The list is defined in one place only (not duplicated across call sites).
- AC-04-2: The list covers at minimum the formatting elements that Tiptap emits by default
  for the editor configuration in use. [VERIFY IN REPO — inspect `frontend/src` to determine
  which Tiptap extensions are active and what tags they produce.]

**Status:** ⚠ DECISION NEEDED — the allowed-tag list must be agreed before implementation
of REQ-01 can be completed.

---

## Out of scope for THES-188

- Sanitizing manuscript titles (plain text, no HTML).
- Front-end sanitization or validation.
- Changes to the data-storage schema.
- Re-sanitizing bodies already in the store.
