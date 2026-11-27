# Design for production RAG

## Design Decisions

| ID | Decision | Affected components | Requirements |
| --- | --- | --- | --- |
| D-001 | Add a production chunker behind the existing chunker interface. Use the embedding model tokenizer to walk 192-content-token windows with stride 160 (32-token overlap), excluding special tokens from the budget, stop at the final token, and retain source text for each chunk. Assign sequential positions and compute SHA-256 over the emitted text. Return an empty list for whitespace at the chunker boundary. | Document chunker, ingestion worker | R-001 |
| D-002 | Supply one local embedding generator to ingestion and chat through the assistant module. Load sentence-transformers/all-MiniLM-L6-v2 and its tokenizer from the same provisioned, revision-pinned local snapshot with remote fetching disabled. Preserve chunk identity and order across batch encoding and use the same vector dimension for queries. | Embedding generator, ingestion worker, chat service, assistant module | R-002 |
| D-003 | At production startup, pass the production chunker, local generator, and a Chroma store opened at the configured persistent path into the container builder. Keep in-memory construction for default test startup and preserve explicit adapter overrides. Exercise storage durability by reopening the same directory through fresh wiring. | Application factory, container builders, Chroma adapter | R-003, R-004 |
| D-004 | Inject the active vector store into the subscribed removal handler. For an indexed source, invoke document-scoped deletion and persist the stale transition. Permit repeated deletion after partial failure and propagate cleanup errors so callers can detect incomplete removal. Preserve the unknown-source return. Serialize final indexing writes and removal per document. Under the same lock, invalidate the active job before cleanup and check job validity before any later vector or status write, including failure handling. | Assistant module, ingestion worker, source-removal handler, indexed document repository, vector store | R-005 |
| D-005 | Use isolated temporary storage and the same pre-provisioned MiniLM snapshot as production and the bicycle-repair and bread-baking passages from S-027 in integration tests. Block and record network attempts during indexing and querying. Inspect vectors directly after removal and use real retrieval to check ranking and persistence. | Assistant test fixtures, ingestion, chat, startup and source-removal tests | R-006, R-002, R-003, R-004, R-005 |

## Verification

Run the scenarios through the component boundary named in the [findings](repo-findings.md). Blank text is a chunker case. Durability requires fresh production wiring. A stale record can hide retained vectors from search, so verify deletion independently of search visibility.
