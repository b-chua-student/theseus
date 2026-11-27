# Implementation tasks — Production RAG

## Dependency graph

```mermaid
flowchart TD
    T001["T-001 Create tests"] --> T002["T-002 Verify baseline"]
    T002 --> T003["T-003 Chunking"]
    T002 --> T004["T-004 Embeddings"]
    T002 --> T005["T-005 Removal"]
    T003 --> T006["T-006 Startup"]
    T004 --> T006
    T005 --> T007["T-007 Verify all scenarios"]
    T006 --> T007
```

## Tasks

| ID | Work item | References | Depends on | Verification | Scenarios | Wave |
| --- | --- | --- | --- | --- | --- | --- |
| T-001 | Create executable scenario tests and offline fixtures before changing application code. Place the scenario tests in `backend/tests/domain/assistant/test_production_rag.py`. | D-001, D-002, D-003, D-004, D-005 | - | Check token limits, overlap, positions and hashes, blank input, ordered vectors, offline ranking, persistence after reopening, test storage isolation, scoped deletion and unknown-source removal. | S-019, S-020, S-021, S-022, S-023, S-024, S-025, S-026, S-027, S-028 | 1 |
| T-002 | Run the new tests against the current implementation and record the baseline. | R-001, R-002, R-003, R-004, R-005, R-006 | T-001 | From `backend/`, run `python -m pytest -q tests/domain/assistant/test_production_rag.py`. Confirm missing behaviors fail for their expected assertions. Record already passing cases. Resolve fixture or model provisioning errors before implementation. | S-019, S-020, S-021, S-022, S-023, S-024, S-025, S-026, S-027, S-028 | 2 |
| T-003 | Implement the production overlapping token chunker. | D-001 | T-002 | Run long-paragraph and blank-input tests. | S-019, S-024 | 3 |
| T-004 | Implement the local embedding generator for ingestion and query use. | D-002 | T-002 | Check order, dimension, paraphrase ranking, and zero outbound attempts. | S-020, S-027 | 3 |
| T-005 | Connect document-scoped vector deletion to source removal. | D-004 | T-002 | Inspect both sources' vectors after removal, check remaining retrieval, and exercise the unknown-source path. Pause indexing before its final writes, complete removal, resume the worker, and verify stale status and zero vectors again. | S-022, S-026, S-028 | 3 |
| T-006 | Wire production adapters and persistent storage while retaining default test wiring. | D-003 | T-003, T-004 | Retrieve an indexed passage through fresh wiring at the same isolated path. Verify test startup leaves production storage untouched. | S-021, S-025 | 4 |
| T-007 | Run all scenario tests together offline and reconcile results with the feature. | D-005, R-001, R-002, R-003, R-004, R-005, R-006 | T-005, T-006 | From `backend/`, run `python -m pytest -q tests/domain/assistant/test_production_rag.py`. Record passing results for every scenario with network access blocked and live credentials absent. | S-019, S-020, S-021, S-022, S-023, S-024, S-025, S-026, S-027, S-028 | 5 |
