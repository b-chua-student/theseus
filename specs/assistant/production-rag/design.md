# Design for production RAG

## Design Decisions

| ID | Decision | Affected components | Requirements |
| --- | --- | --- | --- |
| D-001 | Add a production chunker behind the existing chunker interface. Walk token windows with a positive stride smaller than the window, stop at the final token, and retain source text for each chunk. Assign sequential positions and compute SHA-256 over the emitted text. Return an empty list for whitespace at the chunker boundary. | Document chunker, ingestion worker | R-001 |
| D-002 | Supply one local embedding generator to ingestion and chat through the assistant module. Load the model from a provisioned local artifact with remote fetching disabled. Preserve chunk identity and order across batch encoding and use the same vector dimension for queries. | Embedding generator, ingestion worker, chat service, assistant module | R-002 |
| D-003 | At production startup, pass the production chunker, local generator, and a Chroma store opened at the configured persistent path into the container builder. Keep in-memory construction for default test startup and preserve explicit adapter overrides. Exercise storage durability by reopening the same directory through fresh wiring. | Application factory, container builders, Chroma adapter | R-003, R-004 |
| D-004 | Inject the active vector store into the subscribed removal handler. For an indexed source, invoke document-scoped deletion and persist the stale transition. Permit repeated deletion after partial failure and propagate cleanup errors so callers can detect incomplete removal. Preserve the unknown-source return. | Assistant module, source-removal handler, indexed document repository, vector store | R-005 |
| D-005 | Use isolated temporary storage and a pre-provisioned local semantic model in integration tests. Block and record network attempts during indexing and querying. Inspect vectors directly after removal and use real retrieval to check ranking and persistence. | Assistant test fixtures, ingestion, chat, startup and source-removal tests | R-006, R-002, R-003, R-004, R-005 |

## Verification

Run the scenarios through the component boundary named in the [findings](repo-findings.md). Blank text is a chunker case. Durability requires fresh production wiring. A stale record can hide retained vectors from search, so verify deletion independently of search visibility.
