# Design — Assistant answer validation

## Design

| ID | Decision | Components | Requirements |
| --- | --- | --- | --- |
| D-001 | Gate finalization in ChatService.ask() for source_library requests, including empty retrieval results. Open one exchange per request and reuse its original question through all checks. | ChatService, Conversation, Exchange | R-001, R-002, R-003 |
| D-002 | Add a validation port with a Gemini adapter and a scripted fake. Check relevance and map each claim and inline citation to the exact numbered RetrievedChunk supplied for that draft. Return verified findings, unresolved claims and checked gaps as distinct fields. | ChatModel, GeminiChatModel, validation port, RetrievedChunk | R-001, R-002, R-005, R-009 |
| D-003 | Use feedback to revise the draft or search for the missing evidence. Pass a focused query to retrieval while retaining project and source filters. Merge retrieved chunks by identity and retain stable citation numbers across retries. Distinguish a failed lookup from a successful empty result. | ChatService._retrieve(), embedding and vector-store ports, validation adapter | R-002, R-003, R-010 |
| D-004 | Use one request-local retry counter and a monotonic deadline. Start the clock when the first draft is ready. Charge one retry before each recovery cycle. Bound all waits by the remaining time, and give each adapter call a timeout no longer than the remaining time, because a blocking model call cannot be cancelled. Ignore late results. | ChatService, model and retrieval adapters, injectable clock | R-004, R-007, R-008 |
| D-005 | Build the terminal response from completed checks. Record the accepted answer or verified summary once, including the exhaustion and deadline messages, as the exchange's answer. On a validation service error, discard the pending exchange and return the specified message as an error, not as an answer. | ChatService, ConversationRepository, bootstrap error handlers | R-001, R-005, R-008, R-009, R-010 |
| D-006 | Add an opt-in event stream to the existing exchange request so the server can report progress while validation is pending. Emit progress once after five seconds, suppress it after completion, and send one terminal answer or error. Run validation off the thread that sends progress so a blocking call cannot delay it. Alternative considered: polling a status endpoint. It needs request-scoped job state and extra round trips, so streaming is preferred, with polling as the fallback in requirements.md Open Questions. | conversation blueprint, frontend/src/lib/api/chat.js, ChatPanel.svelte | R-006, R-007, R-008, R-010 |

## Components and Flow

The feature-specific [repository findings](repo-findings.md) identify the insertion point between `ChatModel.reply()` and `conversation.answer()`. The current ticket supplies the timing and retry decisions that were still open when those findings were written.

1. Retrieve evidence and generate the first draft using the existing request scope. Begin validation immediately when that draft is ready. Manuscript-only and general questions retain their existing flow (assumption recorded in requirements.md Open Questions).
2. Check the draft against the original question and its passage list. Reject unsupported claims, irrelevant answers and citations that point to the wrong passage. An accepted draft proceeds to finalization.
3. If time and retries remain, revise, retrieve or do both, then validate again. Retain verified findings from completed checks independently of the current draft.
4. Stop on acceptance, exhaustion, deadline or a blocking service error. A single request owner selects the terminal result and finalizes the exchange. Adapter calls cannot independently save or publish a result.

## Data and Interfaces

Keep `Answer(text)` and the existing JSON exchange response (`201 {answer: text}`) compatible. Citation references are structured inside validation and rendered in the final text. Each reference binds a claim to its passage ID and source location. Unknown or mismatched references fail the check.

Wire the validation port through the assistant module and both container configurations. Preserve the existing two-argument service construction for callers outside the validation path. A source-backed request that cannot obtain its validator follows the validation error flow.

For the interactive chat client, negotiate newline-delimited JSON on the existing authorized POST. Send a status record with the progress message and a terminal record carrying either answer text or a user-facing error. Flush records incrementally. After response headers are sent, represent validation errors with a terminal error record. Keep only the status visible while awaiting the final result. Drive progress and deadline timers independently of blocking model or retrieval calls.

## Evidence Outcomes

A supported May start and July end can be displayed with their respective passages. A draft asserting July 12 or citing the start passage for the end date is withheld until corrected and checked. If only the start can be verified, report it with its citation and explain the unresolved end date.

At the deadline, if no check completed, tell the user the answer could not be checked. If every draft was off-topic at exhaustion, use the relevance message in R-009. A service error uses R-010. Neither outcome alone establishes a gap in the sources.
