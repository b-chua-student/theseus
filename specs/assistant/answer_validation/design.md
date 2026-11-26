# Design — Assistant answer validation

## Design

| ID | Decision | Components | Requirements |
| --- | --- | --- | --- |
| D-001 | Branch in `ChatService.ask()` before the existing model reply. Retrieve within the supplied scope, then attempt a local answer. One exchange owns all attempts from retrieval to finalization. | ChatService, EvidenceRetriever, Conversation | R-001, R-003, R-011, R-012 |
| D-002 | Use the same local checker for directly extracted and Gemini-proposed findings. Accept a finding only when its excerpt belongs to the cited passage and supports the requested fact at the stated precision. For ambiguous questions the generation adapter may propose findings once. It cannot approve its own proposal. | Local checker, Gemini generation adapter, Evidence, Finding | R-001, R-002, R-005, R-009, R-011, R-012, R-013 |
| D-003 | Retry within the original project and selected sources. Keep citation identities stable for retained evidence. Correct references, narrow claims or build a fresh candidate locally from new evidence, then recheck it. Attribute supplied manuscript text separately from library evidence. | EvidenceRetriever, ReviseDraft, local checker | R-002, R-003, R-010, R-013 |
| D-004 | Track three independent limits per exchange: one outbound generation attempt, two recovery cycles after the initial check, and 30 seconds from first draft readiness. Charge the generation attempt before dispatch, including when the provider fails or times out. Disable automatic generation retries in the adapter or SDK. Count embeddings separately. | ChatService, ValidateAnswer, generation adapter, injectable clock | R-004, R-007, R-008, R-011 |
| D-005 | Finalize once. Prefer verified findings. For a deadline with none verified, snapshot eligible pending claims from a proposal received before the cutoff. Track rejected claims separately so retries cannot restore them. Preserve the specified exhaustion, off-topic, deadline and service-error outcomes. Ignore late results. | ValidateAnswer, ConversationRepository, error handlers | R-001, R-005, R-008, R-009, R-010, R-013 |
| D-006 | Preserve the existing JSON and progress-stream contracts. Signal first draft readiness for either path. Emit progress only while validation remains pending beyond five seconds and send one terminal result. | Conversation route, chat API client, ChatPanel | R-006, R-007, R-008, R-010 |

## Components and Flow

1. Retrieve passages and examine whether they directly answer the original question. For the local path, identify the subject, requested relationship and expected detail, such as the pilot's **end month**. Extract only facts with an unambiguous match. Similarity ranks candidate passages; it cannot establish a claim.
2. If local selection is inconclusive and evidence exists, the optional Gemini call receives the question, supplied context and numbered passages. Its proposal includes the candidate findings, exact excerpts and passage keys. If an empty search or a local correction can be handled without generation, keep the allowance unused.
3. Start validation timing when the first candidate draft is ready, whether built locally or proposed by Gemini. Keep the same start time for every retry. Check each claim locally. Reject swapped citations, unsupported precision, conflicting evidence, and excerpts that address the wrong entity or attribute. When a free-form inference cannot be checked, narrow it to a supported finding or explain the uncertainty.
4. Within the two-retry limit, search for missing evidence or revise and recheck locally. Once generation has been attempted, no recovery path can dispatch it again. A blocking service failure before the deadline uses the interruption flow. At the deadline, including a simultaneous failure, use the deadline response. The deadline and progress signal continue to measure validation time.

## Data and Interfaces

Bind each proposed library finding to its own passage identity and exact excerpt. Compare the excerpt with the admitted passage, then verify the relationship between the question, the proposed statement and that excerpt. Construct displayed citations from accepted findings on the server. A manuscript attribution uses the supplied manuscript text; an assertion about a library source needs support from that source.

Expose eligible pending text in an optional terminal response field separate from the answer and verified citations. ChatPanel reveals it only on request with the unverified label. Keep the saved exchange format and the existing status and terminal events. Preserve other context modes. Replace the source-backed sequence of separate draft, check and revision generation calls at the orchestration boundary. Test the outbound generation count with a shared provider spy and track the embedding fake independently.

## Evidence Outcomes

For S-014, two unambiguous excerpts establish the start and end months without generation. For S-015, one proposal selects the pilot end date among similar passages; the local checker verifies it belongs to the pilot rather than the follow-up. For S-016, “ended in July” cannot establish an end year. A subsequent local search may supply the year, otherwise the response identifies it as unverified. For S-017, an interrupted generation attempt still consumes the allowance.

Use the conditional deadline response, the pre-deadline interruption response and the off-topic exhaustion response specified in R-008 through R-010. Preserve verified citations through partial answers and reopened conversations.
