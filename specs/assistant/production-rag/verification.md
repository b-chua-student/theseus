# Production RAG verification — Wave 5

At revision `eae281c`, all **19 tests passed** in 7.36 seconds on Windows with Python 3.12.10. From `backend/`, the command was `python -m pytest -v tests/domain/assistant/test_production_rag.py --tb=short`.

The run used a pre-provisioned MiniLM snapshot with `HF_HUB_OFFLINE=1`, implicit Hugging Face token use disabled, and Gemini, Google, and Hugging Face API key or token variables cleared. The fixture blocked DNS and outbound socket calls during each case. Production startup tests exercised the real local ONNX encoder and persistent vector storage with MongoDB I/O replaced by test fixtures.

| Scenario | Passed cases | Verified outcome |
| --- | ---: | --- |
| S-019 | 2 | Ordered, hashed chunks stay within 192 content tokens and reconstruct the input token sequence with 32-token overlap. |
| S-020 | 2 | Local batch embeddings preserve input order and match individual 384-dimensional embeddings. |
| S-021 | 2 | Fresh application wiring retrieves an indexed passage using either an explicit model path or the local pinned cache. |
| S-022 | 2 | Removal marks the source stale, deletes its vectors, and preserves retrieval from another source. Cleanup succeeds on retry after a vector-store error. |
| S-023 | 1 | Indexing, retrieval, and deletion complete offline, and a direct vector lookup confirms cleanup. |
| S-024 | 4 | Empty and whitespace-only inputs produce no chunks through either adapter or startup wiring. |
| S-025 | 1 | Default test startup indexes and retrieves in memory without creating the production vector directory. |
| S-026 | 1 | Removing a never-indexed source completes without a logged handler exception. |
| S-027 | 2 | The bicycle and bread queries each rank the corresponding passage first using the shared local generator. |
| S-028 | 1 | A worker resumed after removal leaves the document stale with no stored vectors. |

An additional passing case verifies that production startup preserves explicit adapter overrides. See the [acceptance tests](../../../backend/tests/domain/assistant/test_production_rag.py), [Gherkin scenarios](gherkin.feature), and [Wave 2 baseline](baseline.md).
