# [ASSISTANT-RAG-03] As a writer, I can retrieve relevant passages from my source library

## Intent
Help writers find passages by meaning and keep removed sources out of future retrieval.

## Context
Writers upload text sources and ask source-grounded questions. Operators need persistent production retrieval without embedding API quota usage.

## Scope
- Split text into overlapping chunks and generate semantic embeddings locally.
- Persist production vectors and clean up removed sources.
- Preserve fast in-memory test defaults and verify retrieval offline.

## Expected Outcomes
- [ ] Long text yields ordered chunks with sequential positions, content hashes, contextual overlap, and at most the configured number of tokens per chunk. Blank text yields no chunks.
- [ ] Each chunk receives one fixed-dimension vector in input order. A paraphrased query ranks the matching passage ahead of an unrelated passage.
- [ ] Production startup enables token-aware chunking, local semantic embeddings, and persistent vector storage. Automated test startup uses in-memory defaults without writing to production storage.
- [ ] Removing an indexed source marks its record stale and deletes all its vectors. Other sources remain retrievable. Removing a never-indexed source succeeds.
- [ ] Offline checks verify chunking, embedding and retrieval, production and test startup, and source removal.

## Rules / Constraints
Use the same local model for indexing and querying. Once the model is available locally, neither operation makes external network requests or consumes provider embedding quota.

## Non-Functional Requirements
Automated verification runs without network access or live external credentials. Production assumes sufficient host memory for a lightweight local model.

## Out of Scope
Cloud embedding APIs, background indexing queues, multi-process workers, rich binary or PDF parsing, and changes to prompt guardrails, input screening, rate limits, or history caps.

## Open Questions
Should projects choose their own chunk size and overlap? Deferred: fixed defaults suffice for this release.

## Output Paths
Feature directory: `specs/assistant/production-rag/`.

- Intake brief: `brief.md`
- Gherkin: `gherkin.feature`
- Spec files: `requirements.md`, `design.md`, and `tasks.md`

## Definition of Done
- [ ] Intake generated and approved
- [ ] Gherkin generated and approved
- [ ] Open questions resolved
- [ ] Spec, Gherkin, and code in sync
- [ ] Reviewed and merged
