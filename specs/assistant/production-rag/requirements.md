# Requirements — Production RAG

- Ticket: `tickets/assistant-rag.md`

## Requirements

| ID | Requirement | Source | Ticket lines | Scenarios |
| --- | --- | --- | --- | --- |
| R-001 | Split long text into ordered chunks with sequential positions, content hashes, and contextual overlap. Each chunk contains at most 192 content tokens and adjacent windows overlap by 32 content tokens across all projects. Blank text yields no chunks. | from ticket | 15 | S-019, S-024 |
| R-002 | Generate one fixed-dimension vector per chunk in input order. Use the same locally available semantic model for indexing and querying without external requests or provider quota. A paraphrased query ranks the matching passage above an unrelated passage. | from ticket | 16, 22 | S-020, S-027 |
| R-003 | Production startup enables token-aware chunking, local semantic embeddings, and vector storage that preserves indexed passages across startup. | from ticket | 11, 17 | S-021 |
| R-004 | Automated test startup uses fast in-memory defaults and leaves production storage untouched. | from ticket | 12, 17 | S-025 |
| R-005 | Removing an indexed source marks its record stale and deletes all its vectors. Other sources remain retrievable, and removing a never-indexed source succeeds. After removal completes, an in-flight indexing job cannot restore the record to indexed status or recreate its vectors. | from ticket | 18 | S-022, S-026, S-028 |
| R-006 | Automated checks exercise chunking, indexing and retrieval, production and test startup, and source removal offline without live credentials. | from ticket | 19, 25 | S-023 |

## Open Questions

- None.
