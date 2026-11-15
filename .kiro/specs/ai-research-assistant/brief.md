# Brief: AI Research Assistant
ID: THES-160
Owner: John Patrick Panhilason Salugsugan
Date: 2026-11-15
Base SHA: Deferred (see Open Questions)

## Goal
Let project members ask questions about their manuscript and receive answers grounded in its indexed content. Manuscripts and sources are indexed automatically when they change.

## Users / Roles
- Project member: creates conversations, checks indexing status, asks questions.
- System: reacts to manuscript and source changes by indexing and de-indexing content.
- Visitor without a session: has no access to any assistant capability.

## In Scope
- Automatic indexing when a manuscript is saved (THES-161)
- Automatic indexing and de-indexing when a source is added or removed (THES-166)
- Checking whether a manuscript is indexed and searchable (THES-169)
- Creating a conversation within a project (THES-173)
- Asking a question and receiving an answer (THES-177)
- Defined outcomes when the AI provider is busy, failing, or not configured

## Non-Goals
- Streaming or partial answers
- Memory across questions beyond a single conversation
- Switching between AI providers
- Wiring the ChromaDB and PostgreSQL adapters
- Work tracked in THES-189, THES-190, THES-191 (separate, unassigned tickets)

## Constraints
- A question must be 1 to 4000 characters and not blank.
- An answer is returned whole, never streamed.
- Saving a manuscript completes without waiting for indexing to finish.
- A failure while indexing or de-indexing one item does not stop other items from being processed.
- Every capability rejects a request made without a session.
- Status checks and conversation creation by a non-member, or for an unknown project or manuscript, are rejected as not found.
- A busy-provider response tells the caller when to retry.

## Known Touchpoints
Hints only, not verified:
- Assistant services: chat, get_indexing_status, ingestion_worker
- Handlers: on_manuscript_saved, on_source_added, on_source_removed
- Routes under /api/projects/{p}: indexing-status, conversations, exchanges
- Google Gemini as the answering provider; an in-memory vector store

## Assumptions
- The acceptance criteria on THES-161, 166, 169, 173, 177 are the current source of truth.
- The index is held in memory and is lost on restart (per the epic); how it is rebuilt is outside this brief.
- Ticket status codes (400, 401, 404, 409, 429, 502, 503) correspond to the outcomes in the Success Criteria.

## Open Questions
- Base SHA. Deferred: no repository access during intake; add before spec work starts.
- THES-189 names a vector index adapter while the epic excludes the ChromaDB/PostgreSQL adapters. Deferred: separate unassigned ticket; confirm with Bernard Ordanel Chua Jr.
- THES-191 (index reconcile job) is marked pending decision. Deferred: separate ticket; excluded from this brief.
- Exact retry delay for a busy provider. Deferred: not stated in the tickets.
- Indexing status values other than not_indexed. Deferred: not listed in the tickets.

## Success Criteria
1. After a saved manuscript finishes indexing, its status shows searchable with a chunk count above zero.
2. Saving a manuscript returns without waiting for indexing.
3. When indexing or de-indexing one item fails, other items are still processed.
4. Adding a source makes its content indexed; removing a source removes its content from the index.
5. A member checking status sees status, chunk count, and searchable; status is not_indexed until the manuscript is saved and indexed.
6. Searchable is true only when the assistant can retrieve from the manuscript.
7. A non-member, or an unknown project, manuscript, or conversation, gets a not-found result; a request with no session is rejected as unauthorized.
8. A member creating a conversation receives its id.
9. A valid question in a valid conversation returns an answer built from retrieved indexed chunks.
10. A blank query, or one outside 1 to 4000 characters, is rejected with validation details.
11. A question while a previous answer is pending is rejected as a conflict.
12. A busy provider yields a busy result with a retry hint; a provider error yields a provider-error result; a missing configuration yields a not-configured result.

## Reference Links
- https://theseus-inc.atlassian.net/browse/THES-160
- https://theseus-inc.atlassian.net/browse/THES-161
- https://theseus-inc.atlassian.net/browse/THES-166
- https://theseus-inc.atlassian.net/browse/THES-169
- https://theseus-inc.atlassian.net/browse/THES-173
- https://theseus-inc.atlassian.net/browse/THES-177
