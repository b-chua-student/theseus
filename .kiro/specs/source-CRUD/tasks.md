# Implementation Plan: Source Library Text Upload

## Overview

Adds text sources to the source library. Specs: `requirements.md` (R/N), `design.md` (D). Write tests with the code (TDD). Frontend tasks build against the API contract in `design.md`; mock the client until the API layer lands.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1", "10"] },
    { "id": 1, "tasks": ["2", "11", "12"] },
    { "id": 2, "tasks": ["3"] },
    { "id": 3, "tasks": ["4", "5", "7"] },
    { "id": 4, "tasks": ["6", "13"] },
    { "id": 5, "tasks": ["8", "9"] },
    { "id": 6, "tasks": ["14"] }
  ]
}
```

## Tasks

- [x] 1. Value objects
  - Files: `models/value_objects.py` (+ tests)
  - Add `Description`, `Tags`, `ContentType`, `TextBody` with limits and normalization.
  - Done when boundary tests pass (1000/1001 description, 10/11 tags, 0/1/100000/100001 body).
  - _Requirements: R1, R2_

- [x] 2. Aggregate and events
  - Files: `models/aggregates.py`, `models/events.py`
  - Add `kind`, text fields, `version`, `updated_at`; make `file_ref` optional with invariants (D6); add `update_text()`, `SourceUpdated`, and `kind` on `SourceAdded`.
  - Done when invariants and version bump are unit-tested and existing aggregate tests still pass.
  - _Requirements: R1, R5, N4_

- [x] 3. Port and in-memory repository
  - Files: `infrastructure/ports/source_repository.py`, in-memory adapter
  - Add `list_text`, `search_text`, and update-capable `save`. Project-scoped; exclude removed.
  - Done when adapter tests cover filter, sort, paging, search, isolation.
  - _Requirements: R4, R6, R7, R8_

- [x] 4. Mongo adapter
  - Files: Mongo source adapter, index setup
  - Implement the task 3 port; projection excludes `content`; indexes per design (check/extend existing text index); old docs map to defaults.
  - Done when shared adapter contract tests pass against Mongo and a legacy doc loads as `kind=file`.
  - _Requirements: R4, R7, N4_

- [x] 5. Services and wiring
  - Files: `services/*`, container wiring
  - `AddTextSource`, `UpdateTextSource`, `ListTextSources`, `SearchTextSources`; reuse `GetSource`/`RemoveSource`. Emit events.
  - Done when service tests with the in-memory repo pass and events are asserted.
  - _Requirements: R1, R2, R3, R4, R5, R6, R7, R11_

- [x] 6. API layer
  - Files: `api/routes.py`, `api/requests.py`, `api/errors.py`, limiter config
  - Six `/text` endpoints per design; Pydantic request; DTO mapping; 400/404/429; body cap (D8); register `/text/search` before `/text/<id>`.
  - Done when Flask-client tests per endpoint pass, including 401 and foreign-project 404.
  - _Requirements: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10_

- [x] 7. Assistant integration
  - Files: `on_source_added.py`, new `on_source_updated.py`, `on_source_removed.py`, `source_content_provider.py`, `ingestion_worker.py`
  - Text ingest from `content`; reindex on update; drop on remove. Verify `file_ref` assumptions first.
  - Done when handler tests (add/update/remove) pass and the file-source path is unchanged.
  - _Requirements: R11_

- [x] 8. API feature tests
  - Files: step definitions for `source_library_text_upload.feature` (non-`@ui`, non-perf tags)
  - Done when all API-level scenarios, including `@grounding`, are green on in-memory adapters.
  - _Requirements: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11_

- [x] 9. Mongo integration and performance
  - Run key scenarios on Mongo; `@performance` (10 KB < 2 s, 1,000 docs search < 1 s), `@concurrency`, `@storage` (100K round-trip).
  - Done when N1–N3 and N5 are verified and limiter thresholds are tuned.
  - _Requirements: R9_

- [x] 10. Frontend client and types
  - Files: `lib/api/textSources.ts`, types
  - Typed client and DTOs per design; error mapping to field errors.
  - Done when unit tests against mocked fetch pass.
  - _Requirements: R12_

- [x] 11. Frontend form
  - Files: `components/text-sources/TextSourceForm.svelte`
  - Fields, counter, preview (`<pre>`, no `{@html}`), client-side limits, draft autosave/restore, create and edit modes, field errors.
  - Done when component tests for counter, preview, draft restore, validation pass.
  - _Requirements: R1, R2, R5, R12_

- [x] 12. Frontend list, search, edit, delete
  - Files: `TextSourceList.svelte`, `TextSourceCard.svelte`, delete confirm, route wiring
  - Cards, pagination, search, filter, sort, open/edit, delete confirm, empty state.
  - Done when component tests pass and text sources appear in the main library list.
  - _Requirements: R4, R6, R7, R12_

- [x] 13. Accessibility and responsive layout
  - Labels, keyboard path, `aria-live` errors, focus management, breakpoints.
  - Done when axe checks are clean, the manual keyboard pass succeeds, and mobile/tablet/desktop layouts work.
  - _Requirements: R12_

- [x] 14. UI scenarios
  - Bind `@ui @accessibility @responsive` scenarios (Playwright or the repo's e2e tool).
  - Done when the full feature file is green.
  - _Requirements: R12_

## Notes

- Critical path: 1 → 2 → 3 → 5 → 6 → 8 → 14.
- Original T-numbering maps directly to task numbers (T1 = 1). A backup is in `tasks.backup.md`.
