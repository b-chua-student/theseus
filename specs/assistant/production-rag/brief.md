# Brief: Production RAG Pipeline, Local Embeddings, and Vector Cleanup

- ID: ASSISTANT-RAG-03
- Owner: AI Engineer (Theseus)
- Date: 2026-11-27
- Base SHA: 16ef0610636dbc8786f1a95d65bea5a257ab3196

## Goal

Replace the assistant's placeholder in-memory RAG adapters with a real production retrieval pipeline using token-aware overlapping chunking, local zero-quota semantic embeddings, persistent vector storage, and automatic vector cleanup when sources are removed.

## Users / Roles

- Writer uploading sources and asking source-grounded questions in source library scope.
- Operator deploying the assistant with persistent storage and zero embedding API quota usage.

## In Scope

- Split document text into ordered, token-sized chunks with overlap, position metadata, and content hashes.
- Generate semantic embeddings locally on the host without calling external AI APIs or consuming provider quota.
- Wire the real chunker, local embedding generator, and persistent vector store into production application startup while keeping in-memory defaults in automated tests.
- Delete a source's stored vectors from the vector store whenever that source is removed from the library.
- Verify chunking, local embedding generation, production wiring, and vector cleanup through offline automated tests.

## Non-Goals

- Calling external cloud embedding APIs or consuming external AI provider quota for embeddings.
- Asynchronous background indexing queues or multi-process workers.
- Rich PDF or binary file parsers beyond existing text content handling.
- Changing prompt guardrails, input screening, rate limits, or history caps from prior specs.

## Constraints

- Embedding generation must produce one vector per input chunk in the same order and use the same model for both indexing and querying.
- Local embedding generation must not make external network requests during normal indexing or query embedding once the model is available, and unit tests must run fully offline.
- Automated test containers must continue using fast in-memory defaults without writing to production storage paths.
- Removing a source must mark its indexed record stale and remove its vectors without failing if the source was never indexed.

## Known Touchpoints

- Assistant document chunker, embedding generator, and vector store adapters.
- Assistant source-removal event handler and module wiring.
- Application bootstrap production container wiring and offline assistant tests.

## Assumptions

- Production runs on a host with sufficient local memory for a lightweight local semantic embedding model.


## Open Questions

- Should chunk size and overlap be configurable per project? Resolved. All projects use a 192-content-token budget and a 32-token overlap.

## Success Criteria

1. Document chunking splits non-empty text into ordered overlapping chunks within the configured token budget with content hashes and returns an empty list for blank text.
2. Local semantic embedding generation returns one consistent fixed-dimension vector per chunk in order without calling external AI APIs. A paraphrased query ranks the matching passage above an unrelated passage.
3. Production application wiring uses the real chunker, local embedding generator, and persistent vector store, while test wiring preserves in-memory defaults.
4. Removing a source deletes its vectors from the vector store while leaving other sources retrievable. Removing an unindexed source succeeds. If removal occurs during indexing, the source stays stale with no stored vectors after both operations finish.
5. Automated offline tests verify chunking, local embedding behavior, production vs. test wiring, and source-removal vector cleanup without external credentials or network calls.

## Reference Links

- Source ticket: [assistant-rag.md](../../../tickets/assistant-rag.md)
- Prior specs: specs/assistant/prompt-guardrails/brief.md, specs/assistant/chat-safeguards/brief.md
- Repository SDD workflow: AGENTS.md
