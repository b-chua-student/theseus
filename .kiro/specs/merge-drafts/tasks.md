# Implementation Plan: merge-drafts

## Overview

Backend work is Python under `backend/domain/revision_history` and `backend/bootstrap`; frontend work is Svelte/JS under `frontend/src`. Tasks are ordered so each builds on earlier ones: domain types and errors, pure merge engine, aggregate, persistence, event and writer, service, API, docs, then frontend. Each task lists only the files it touches. Backend paths are relative to `backend/`, frontend paths to `frontend/src/`. Test sub-tasks are optional. Property tests use Hypothesis with at least 100 examples and a `# Feature: merge-drafts, Property N: <title>` comment.

## Tasks

- [x] 1. Domain value objects and errors
  - [x] 1.1 Add `MergeSource` and `Revision.merged_from`
    - Files: `domain/revision_history/models/value_objects.py`, `domain/revision_history/models/entities.py`
    - Add frozen `MergeSource(draft_name, head_revision_id)`. Add `merged_from: MergeSource | None = None` to `Revision` after `created_at`.
    - _Requirements: 2.3_
  - [x] 1.2 Add merge error classes
    - Files: `domain/revision_history/models/errors.py`
    - Add `DraftNotFoundError`, `NoSharedHistoryError`, `UnsavedChangesError`, `MergeConflictError(conflicts)`, `InvalidResolutionError(kind, section_id, field)`, `MergeInProgressError`, `ConcurrentModificationError`, all under `RevisionError`, with the codes from the design. Make `_branch` in the aggregate unchanged for now (done in 3.1).
    - _Requirements: 1.10, 2.5, 4.6, 5.6, 5.7, 5.10, 6.1, 6.4_

- [x] 2. Pure merge engine
  - [x] 2.1 Merge types, normalization and conflict detection
    - Files: `domain/revision_history/models/merge.py` (new)
    - Define `Choice`, `Resolution`, `Conflict`, `Merged`, `Conflicts`, `normalize` (sibling-rank ordinals, pre-order, ties by id), `merge3`, and `detect_conflicts` (field conflicts and deletion conflicts, sorted by `(section_id, field)`).
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 4.1, 4.2, 4.7, 4.8_
  - [x] 2.2 Resolutions, structural validation and `merge_snapshots`
    - Files: `domain/revision_history/models/merge.py`
    - Apply resolutions (including deletion keep/delete with descendants), detect `parent_cycle` and `parent_missing` on the result, return `Conflicts` or `Merged` with ordinals renumbered.
    - _Requirements: 3.9, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.8, 5.9_
  - [ ]* 2.3 Write property test for field-level merge rule
    - Files: `tests/domain/revision_history/test_merge_property_fields.py` (new)
    - **Property 1: Field-level merge rule**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 4.8**
  - [ ]* 2.4 Write property test for well-formed merged snapshot
    - Files: `tests/domain/revision_history/test_merge_property_wellformed.py` (new)
    - **Property 2: Merged snapshot is well formed**
    - **Validates: Requirements 3.9, 10.3**
  - [ ]* 2.5 Write property tests for identity and fast-forward
    - Files: `tests/domain/revision_history/test_merge_property_identity.py` (new)
    - **Property 3: Merging a draft with no new changes is rejected** (engine part)
    - **Property 4: Fast-forward**
    - **Validates: Requirements 3.12, 3.13, 10.2**
  - [ ]* 2.6 Write property test for conflict detection
    - Files: `tests/domain/revision_history/test_merge_property_conflicts.py` (new)
    - **Property 5: Conflicts are detected exactly when both sides diverge**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
  - [ ]* 2.7 Write property test for determinism
    - Files: `tests/domain/revision_history/test_merge_property_determinism.py` (new)
    - **Property 6: Merge computation is deterministic**
    - **Validates: Requirements 2.6, 4.7**
  - [ ]* 2.8 Write property test for resolutions
    - Files: `tests/domain/revision_history/test_merge_property_resolutions.py` (new)
    - **Property 7: Resolutions select the chosen side**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

- [x] 3. Aggregate
  - [x] 3.1 Add version, base selection, `plan_merge` and `attach`
    - Files: `domain/revision_history/models/aggregates.py`
    - Add `version: int = 0` (set in `rehydrate`), `find_merge_base`, `plan_merge` (self-merge check, `NoChangesError` on both no-change cases, `MergeConflictError`, unattached `Revision` with `merged_from`, default message), `attach`. Make `_branch` raise `DraftNotFoundError`.
    - _Requirements: 1.2, 1.6, 1.7, 1.8, 1.9, 1.10, 1.12, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.10, 3.11_
  - [ ]* 3.2 Write property test for base selection
    - Files: `tests/domain/revision_history/test_merge_property_base.py` (new)
    - **Property 8: Base revision selection matches a reference model**
    - **Validates: Requirements 2.1, 2.2, 2.4**
  - [ ]* 3.3 Write unit tests for aggregate merge rules
    - Files: `tests/domain/revision_history/test_plan_merge.py` (new)
    - Cover 1.10, 1.12, 2.4 rename, 2.5 no shared history, 3.10, 3.11, message length 1.8 with hand-built histories.
    - _Requirements: 1.8, 1.10, 1.12, 2.4, 2.5, 3.10, 3.11_

- [x] 4. Repository version and persistence
  - [x] 4.1 In-memory repository version check
    - Files: in-memory `RevisionHistoryRepository` adapter under `domain/revision_history/adapters/`
    - Track a per-manuscript stored version. `save` raises `ConcurrentModificationError` on mismatch, then bumps `history.version`.
    - _Requirements: 6.4_
  - [x] 4.2 Mongo repository: `merged_from` and `version`
    - Files: `domain/revision_history/adapters/mongodb_revision_history_repository.py`
    - Persist optional `merged_from` on revision documents and `version` on history documents (absent reads as 0). `replace_one` filters on `{_id, version: v}` (for v == 0 also match missing); `matched_count == 0` or duplicate key raises `ConcurrentModificationError`.
    - _Requirements: 2.3, 6.4_
  - [ ]* 4.3 Write unit tests for repository versioning and round trips
    - Files: `tests/domain/revision_history/test_repository_version.py` (new)
    - Stale save raises, `merged_from` and `version` round trip, old documents without the fields read back as `None` and 0.
    - _Requirements: 2.3, 6.4_

- [x] 5. Content-replaced event and writer
  - [x] 5.1 Add `ManuscriptContentReplaced` and emit from `replace_sections`
    - Files: `domain/manuscript/models/events.py`, `domain/manuscript/models/aggregates.py` (the aggregate defining `replace_sections`)
    - _Requirements: 7.9_
  - [x] 5.2 Writer publishes event; wire bus and assistant subscription
    - Files: `ManuscriptRepositoryWriter` adapter in `domain/revision_history/adapters/`, `bootstrap/` container (`build_container`), assistant module (`build_assistant_module`)
    - Writer takes an `EventPublisher`, skips save and event when the snapshot equals the stored one, otherwise saves and publishes `pull_events()`. Subscribe `on_manuscript_saved` to `ManuscriptContentReplaced`.
    - _Requirements: 7.9, 7.10_
  - [x]* 5.3 Write unit tests for event publishing
    - Files: `tests/domain/revision_history/test_writer_events.py` (new)
    - A recording publisher sees exactly one event on change and none on an identical snapshot.
    - _Requirements: 7.9, 7.10_

- [x] 6. Merge service
  - [x] 6.1 Implement `MergeLocks` and `MergeDraftService`
    - Files: `domain/revision_history/services/merge_draft.py` (new)
    - Check order from the design: lock, history, manuscript, message length, unsaved changes, source exists and differs, validate resolutions against `detect_conflicts`, `plan_merge`, apply snapshot, attach and save. On save failure re-apply the earlier working snapshot (log if that fails) and re-raise.
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.8, 1.9, 1.11, 4.5, 5.5, 5.6, 5.8, 5.9, 6.1, 6.2, 6.3, 6.4, 6.5_
  - [x] 6.2 Wire the service into the module
    - Files: `bootstrap/contexts/revision_history/module.py`
    - Construct a shared `MergeLocks` and `MergeDraftService`, expose it to the routes.
    - _Requirements: 6.4_
  - [ ]* 6.3 Write property tests for atomicity and postconditions
    - Files: `tests/domain/revision_history/test_merge_service_properties.py` (new)
    - **Property 9: Rejected merges change nothing**
    - **Property 10: Successful merge postconditions**
    - **Property 3: Merging a draft with no new changes is rejected** (service part)
    - **Validates: Requirements 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.3, 4.5, 5.8, 5.9, 6.1, 6.3**
  - [ ]* 6.4 Write unit tests for the service
    - Files: `tests/domain/revision_history/test_merge_draft_service.py` (new)
    - Conflicting merge leaves history and working copy identical (10.4); invalid and unmatched resolutions; missing manuscript (6.2); two threads with a barrier add exactly one revision (6.4, 6.5); save failure restores the working copy (6.3).
    - _Requirements: 5.5, 5.6, 5.7, 5.10, 6.2, 6.3, 6.4, 6.5, 10.4_

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Merge API
  - [x] 8.1 Request models
    - Files: `domain/revision_history/api/requests.py`
    - Add `ResolutionRequest` and `MergeDraftRequest` (message 1 to 256, up to 1000 resolutions, reject duplicate `(section_id, field)`).
    - _Requirements: 5.7, 5.10, 7.1, 7.3_
  - [x] 8.2 `POST /<name>/merge` route
    - Files: `domain/revision_history/api/routes.py`
    - `@login_required`, validation errors to 422 with `details`, 404 wording for history vs manuscript, success returns `_draft(draft, current=True)`.
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.8_
  - [x] 8.3 Error handler mappings
    - Files: `bootstrap/error_handlers.py`
    - 404 for `DraftNotFoundError`; 409 for `NoChangesError`, `UnsavedChangesError`, `MergeInProgressError`, `ConcurrentModificationError`; 409 with `conflicts` list for `MergeConflictError`; 422 for `InvalidResolutionError`.
    - _Requirements: 4.6, 5.6, 5.7, 5.10, 7.5, 7.6, 7.7, 7.8_
  - [ ]* 8.4 Write API tests
    - Files: `tests/domain/revision_history/test_merge_api.py` (new)
    - 200, 404 (history, draft), 409 (conflicts with full list, no_changes, unsaved_changes), 422 (bad message, bad choice, duplicate, unmatched, over 1000 resolutions), asserting status codes.
    - _Requirements: 7.2, 7.3, 7.5, 7.6, 7.7, 7.8, 10.5_

- [x] 9. Documentation
  - [x] 9.1 Document the merge endpoint
    - Files: `docs/api.md`
    - Add a merge subsection under Drafts: request, 200, and every error response.
    - _Requirements: 7.11_
  - [x] 9.2 Document merge semantics
    - Files: `docs/architecture.md`
    - Extend "Version control model" with base selection, field-level merge, conflicts, atomicity.
    - _Requirements: 7.12_

- [x] 10. Frontend API layer and helpers
  - [x] 10.1 Keep conflict details in `apiFetch` errors
    - Files: `frontend/src/lib/api/http.js`
    - Attach `conflicts` and `details` from the error body to the thrown error.
    - _Requirements: 4.6, 9.1_
  - [x] 10.2 Add `mergeDraft` API call
    - Files: `frontend/src/lib/api/drafts.js`
    - `mergeDraft(projectId, manuscriptId, sourceName, { resolutions, message })` with a 30 s `AbortSignal.timeout`.
    - _Requirements: 7.1, 8.8, 8.13_
  - [x] 10.3 Add merge helpers
    - Files: `frontend/src/lib/mergeDraft.js` (new)
    - `conflictKey`, `carryOverChoices`, `toResolutions`, `valuePreview` (parse tiptap JSON body text, truncate to 200 characters).
    - _Requirements: 9.1, 9.4, 9.5_
  - [x]* 10.4 Write unit tests for helpers
    - Files: `frontend/src/lib/mergeDraft.spec.js` (new)
    - Example tests for `carryOverChoices`, `toResolutions` and `valuePreview`.
    - _Requirements: 9.4, 9.5_

- [x] 11. Merge panel
  - [x] 11.1 Implement `MergePanel.svelte`
    - Files: `frontend/src/components/editor/MergePanel.svelte` (new)
    - Dialog with source select, read-only target, unsaved-changes message, progress state, conflict fieldsets with two radios each (accessible names include heading and field), carry-over of choices, error and `no_changes` messages, Escape to close, source change clears state.
    - _Requirements: 8.5, 8.6, 8.7, 8.8, 8.9, 8.11, 8.12, 8.13, 8.14, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9_
  - [ ]* 11.2 Write component tests for the panel
    - Files: `frontend/src/components/editor/MergePanel.spec.js` (new)
    - Conflict flow (display, select all, submit once), unsaved message, `no_changes`, generic error keeps state, Escape sends no request, source change clears choices, radio accessible names.
    - _Requirements: 8.7, 8.11, 8.12, 8.13, 8.14, 9.2, 9.3, 9.6, 9.7, 9.8, 9.9, 10.7_

- [x] 12. Editor wiring
  - [x] 12.1 Enable the Merge button in `EditorHeader.svelte`
    - Files: `frontend/src/components/editor/EditorHeader.svelte`
    - Add `hasUnsavedChanges` and `onMerge` props, `mergeDisabledReason`, open `MergePanel` (loading drafts if needed), on success reload drafts, close and call `onMerge`. Remove the `TODO(API): MERGE` comment and the "Merge is not implemented" title.
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.10, 8.15_
  - [x] 12.2 Dirty tracking and merge notice in the editor page
    - Files: `frontend/src/pages/editor.svelte`
    - Add `dirty` (set on editor update, cleared after `setContent` in `loadManuscript` and after a successful save), pass `hasUnsavedChanges`, implement `onMerge` to reload and set the notice `Merged "source" into "target".`
    - _Requirements: 8.10, 8.11_
  - [x]* 12.3 Write component tests for the Merge button states
    - Files: `frontend/src/components/editor/EditorHeader.spec.js` (new)
    - Enabled with two drafts, tracking started and no operation in progress; disabled with the expected title for the other three states.
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 10.6_

- [x] 13. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP.
- Adapter and test file locations marked "under" a directory should be confirmed against the repository layout when the task starts.
- Property tests validate universal correctness properties; unit tests cover examples and edge cases.
- Frontend component tests use Vitest and `*.spec.js`; backend tests use pytest and Hypothesis.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "5.1", "10.1", "10.2", "10.3"] },
    { "id": 1, "tasks": ["2.1", "5.2", "10.4", "11.1"] },
    { "id": 2, "tasks": ["2.2", "5.3", "11.2", "12.1"] },
    { "id": 3, "tasks": ["3.1", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "12.2", "12.3"] },
    { "id": 4, "tasks": ["4.1", "4.2", "3.2", "3.3"] },
    { "id": 5, "tasks": ["6.1", "4.3", "8.1"] },
    { "id": 6, "tasks": ["6.2", "6.3", "6.4", "8.3"] },
    { "id": 7, "tasks": ["8.2"] },
    { "id": 8, "tasks": ["8.4", "9.1", "9.2"] }
  ]
}
```


### Implementation verification

Implemented the required backend, API, documentation, and frontend tasks. Added focused tests
in `backend/tests/domain/revision_history/test_merge.py` (including 100-example property tests),
plus `MergePanel.spec.js`, `EditorHeader.spec.js`, and `mergeDraft.spec.js`.
Optional test tasks remain unchecked when their full specified coverage is not present.
The frontend build and tests pass; full frontend lint has a pre-existing
`svelte/prefer-svelte-reactivity` error in `TextSourceForm.svelte`.
