# Production RAG baseline — Wave 2

Application revision `0eb19a7`. From `backend/`, run `python -m pytest -q tests/domain/assistant/test_production_rag.py`.

**7 failed, 4 passed** across ten scenarios. Model provisioning succeeded before the fixture blocked network access. All failures occurred at behavioral assertions.

| Scenario | Result | Observed behavior |
| --- | --- | --- |
| S-019 | Failed | A chunk contained 240 content tokens against the 192-token budget. |
| S-020 | Failed | The generator returned 32 dimensions. The selected MiniLM model produces 384. |
| S-021 | Failed | Fresh production wiring returned zero passages for the previously indexed source. |
| S-022 | Failed | Removal marked the record stale but left its vectors in the store. |
| S-023 | Failed | The offline flow indexed and retrieved a passage. A direct vector query still found it after removal. |
| S-024 | Passed twice | Empty input and whitespace-only input both produced zero chunks. |
| S-025 | Passed | Default test startup indexed and retrieved in memory without creating the production vector path. |
| S-026 | Passed | Removal of a never-indexed source completed without a logged handler exception. |
| S-027 | Failed | Both the bicycle and bread questions ranked the bicycle passage first. |
| S-028 | Failed | After removal, the resumed indexing job left the record indexed instead of stale. |

The initial run had six failures and five passes. The hash-based generator happened to rank the bicycle passage first for the original bicycle question. The recorded baseline retains that question and adds a bread question against the same passages to check that ranking responds to meaning.
