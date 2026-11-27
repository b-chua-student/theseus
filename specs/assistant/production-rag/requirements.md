# Requirements for production RAG

## Sources

- Ticket: `tickets/assistant-rag.md`
- Repository evidence: [repo-findings.md](repo-findings.md), lines 7–19. The findings describe a source inspection at `260474b`.

## Requirements

| ID | Requirement | Source | Ticket lines | Scenarios |
| --- | --- | --- | --- | --- |
| R-001 | Split long text into ordered chunks with sequential positions, content hashes, and contextual overlap. Each chunk fits the token budget. Blank text yields no chunks. | from ticket | 15 | S-019, S-024 |
| R-002 | Generate one fixed-dimension vector per chunk in input order. Use the same locally available semantic model for indexing and querying without external requests or provider quota. A paraphrased query ranks the matching passage above an unrelated passage. | from ticket | 16, 22 | S-020, S-027 |
| R-003 | Production startup enables token-aware chunking, local semantic embeddings, and vector storage that preserves indexed passages across startup. | from ticket | 11, 17 | S-021 |
| R-004 | Automated test startup uses fast in-memory defaults and leaves production storage untouched. | from ticket | 12, 17 | S-025 |
| R-005 | Removing an indexed source marks its record stale and deletes all its vectors. Other sources remain retrievable, and removing a never-indexed source succeeds. | from ticket | 18 | S-022, S-026 |
| R-006 | Automated checks exercise chunking, indexing and retrieval, production and test startup, and source removal offline without live credentials. | from ticket | 19, 25 | S-023 |

## Open Questions

- The findings do not specify the token budget, overlap size, or local model artifact. Record the selected defaults and offline fixture when implementing.
- The findings describe a skip during active indexing. The expected outcome for removal during an in-flight indexing job needs clarification before adding a separate acceptance case.
