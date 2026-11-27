# Tasks

## Task table

| ID | Task | References | Dependencies | Wave | Scenarios |
| --- | --- | --- | --- | --- | --- |
| T-001 | Complete. Instruction obligations, fixed filter thresholds, and the three S-009 examples are recorded in requirements.md. | R-001, R-006 | - | 1 | - |
| T-002 | Set up an offline provider substitute with a dummy key, capture outgoing requests, and disable external network access. | D-004 | - | 1 | S-005 |
| T-003 | Write executable checks for default configuration, none-scope instructions and history, final source and manuscript boundaries, embedded boundary text, empty inputs, and answer delivery in all three scopes. Run them before editing application code. Record existing passes and confirm missing behavior fails on the intended assertions. | D-001, D-002, D-003, D-004, D-005 | T-001, T-002 | 2 | S-001, S-002, S-003, S-004, S-005, S-006, S-007, S-008, S-009 |
| T-004 | Apply the confirmed request defaults and verify explicit instruction overrides. | D-001 | T-003 | 3 | S-001, S-002, S-008 |
| T-005 | Implement reference boundary encoding and apply it to retrieved locations and excerpts. Preserve the question and no-excerpt behavior. | D-002 | T-003 | 3 | S-003, S-006 |
| T-006 | Apply the boundary convention from T-005 to manuscript assembly and preserve the empty-manuscript behavior. | D-003 | T-005 | 4 | S-004, S-007 |
| T-007 | Run all scenario checks with external networking unavailable. Verify controlled answer delivery and saved exchanges in every scope, run existing assistant regressions, and record results by scenario ID. | D-001, D-002, D-003, D-004, D-005 | T-004, T-006 | 5 | S-001, S-002, S-003, S-004, S-005, S-006, S-007, S-008, S-009 |

## Dependency graph

```mermaid
flowchart TD
    T001["T-001 Confirm acceptance values"] --> T003["T-003 Write and run scenario tests"]
    T002["T-002 Prepare offline tests"] --> T003
    T003 --> T004["T-004 Configure defaults"]
    T003 --> T005["T-005 Isolate source excerpts"]
    T005 --> T006["T-006 Isolate manuscript text"]
    T004 --> T007["T-007 Verify all scenarios"]
    T006 --> T007
```
