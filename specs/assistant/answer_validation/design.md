# Design — Assistant answer validation

## Design

| ID | Decision | Components | Requirements |
| --- | --- | --- | --- |
| D-001 | Authorize the conversation and current source selection, then retrieve before looking up a reviewed answer. Distinguish a successful empty search from a retrieval failure. | Conversation route, ChatService, EvidenceRetriever | R-001, R-003, R-010, R-012, R-014 |
| D-002 | On a miss, draft once. Ask Gemini separately to judge relevance and each claim against the original question and numbered passages. Validate returned passage identities and exact excerpts before displaying a finding. | AnswerProposer, AnswerValidator, GeminiAnswerValidator, Evidence | R-001, R-002, R-005, R-009, R-013 |
| D-003 | The draft may identify missing evidence. Use up to two scoped recovery searches before review, preserving citation keys. Review narrowed claims and corrected citations within that same review response. | EvidenceRetriever, Evidence, ValidateAnswer | R-002, R-003, R-004, R-005, R-013 |
| D-004 | Charge each stage before provider dispatch and disable SDK resends for both stages. Start the validation clock at draft readiness. Bound recovery and review by the remaining time and ignore late results. | ChatService, ValidateAnswer, Gemini adapter, monotonic clock | R-004, R-007, R-008, R-011 |
| D-005 | Record one terminal outcome. Keep reviewed findings, rejected claims and pending claims distinct. Handle off-topic, interruption, exhaustion and deadline outcomes under R-005 and R-008 through R-010. | ValidateAnswer, Answer, ConversationRepository, error handlers | R-001, R-005, R-008, R-009, R-010 |
| D-006 | Preserve JSON and streaming responses. Signal draft readiness once, emit progress only after five seconds while checking, and deliver one terminal result with eligible pending text in its separate optional field. | Conversation route, chat client, ChatPanel | R-006, R-007, R-008, R-010 |
| D-007 | Use a bounded, thread-safe, per-worker cache of immutable fully reviewed successes. Match inputs exactly and publish an entry only after a successful exchange save. | ReviewedAnswerCache, ChatService, assistant bootstrap | R-011, R-012 |

## Components and Flow

1. Resolve authorized project, conversation and source scope for every request. A retrieval exception follows the interruption flow. A successful empty search ends with an insufficient-evidence explanation. Neither dispatches generation or serves an old answer.
2. Look up the exact inputs. On a valid hit return the reviewed answer with citations through the normal exchange lifecycle. On a miss, call the draft stage once with the question and evidence. Draft failure consumes that attempt and ends the exchange.
3. Start the validation deadline when the draft is ready. If recovery is needed, fetch evidence within the same selected sources before the review call. Send Gemini the original question, admitted passages and draft. Treat passage content as data. A finding must address the question, identify the correct entity or group, and carry a valid supporting citation. Keep supplied manuscript attribution separate in S-012.
4. Finalize from reviewed findings. Once the review attempt is spent, narrowing and formatting can use only what that review supports. There is no further Gemini revision or recheck. Pre-deadline service failure follows the interruption rule. A failure at the cutoff uses the deadline rule.

## Data and Interfaces

Build a cache key from the authorized project and conversation, exact question, selected source scope, ordered passage identities, text and displayed citation metadata, relevant inputs actually supplied to drafting or review, and model/prompt/review configuration versions. Use a deterministic structured representation. A bounded cache evicts older entries and can miss after a worker restart. Concurrent requests must never see partially written entries.

For a success that used recovery, retain the recovery queries and evidence fingerprints with the entry. Replay the scoped retrieval and compare all evidence used before serving a hit. On any mismatch, discard the candidate hit and use fresh evidence. Count matching recovery work toward the recovery allowance and reuse its results within the exchange. Search embeddings are accounted for separately from generation. Never cache partial findings, interruptions, timeout responses or unverified drafts.

Keep the terminal answer text and verified citation list separate from optional unverified text. Only decisions available before cutoff count. If review is still in flight, its unfinished claims remain pending; an incomplete provider payload cannot establish support. The panel reveals eligible text only on selection with its unverified label. Changing persistence of unverified drafts is outside this design.

## Evidence Outcomes

A review can correct the group size of 25 to the reviewed enrollment total of 75 with the matching passage (S-015). A passage giving only a month cannot support an end year (S-016). At timeout prefer verified findings, otherwise offer only eligible pending claims, otherwise use the timeout message (S-008, S-009, S-013, S-018, S-019). A fully reviewed hit uses zero calls; a fresh success uses two; a failed draft consumes one and a failed review consumes the second. Changed evidence or an ineligible previous outcome cannot authorize reuse (S-014, S-017, S-020, S-021).
