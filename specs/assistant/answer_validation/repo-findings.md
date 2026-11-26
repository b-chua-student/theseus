# Repo findings — assistant answer validation (#125)

The ticket is `tickets/assistant-answer-validation.md`. The brief and Gherkin live alongside this file. The scenario mapping covers S-001 through S-019.

## Current implementation

The application wires `ChatService.ask()` to retrieve scoped Source Library passages and try a locally checked answer. `SourceAnswerCandidates.local()` can produce a direct answer without generation. If local selection is inconclusive, the assisted path can use one Gemini generation attempt per exchange. Embeddings are counted separately. Retry searches and local revisions share the existing two-retry limit.

`GeminiAnswerValidator.propose()` returns individual proposed claims with passage references and excerpts. In `services/source_answer_candidates.py`, `assisted()` obtains the proposal, calls `check_evidence()`, then returns the rendered answer and verdict together. The deadline handler cannot currently see a proposal that arrived while its local check is still running.

In `services/answer_validation.py`, `ValidateAnswer` tracks verified findings and bounds work by the 30-second deadline from first draft readiness. Today its deadline handler returns cited partial findings when available and the timeout message otherwise. The exchange route supports JSON and a progress stream with one terminal result. The chat client and panel currently consume the answer and its citations.

## Work identified by the updated specs

- Capture proposal arrival and claim-level decisions within the exchange. Only a proposal received before the cutoff can supply pending text. A late result cannot change the terminal response.
- Prefer verified findings at the deadline. When nothing was verified, offer only claims still awaiting a check. Exclude claims already found unsupported or off-topic, including during earlier checks. If no eligible text remains, use the existing timeout message.
- Carry eligible text separately from verified findings and citations in JSON and the terminal stream record. Keep it out of progress messages. The panel should keep it collapsed until the writer selects “View unverified draft” and label it unverified when opened.
- The fallback uses the existing proposal. It requires no additional generation attempt. A service failure before the deadline still uses the interruption response.
- Whether to offer the draft again in reopened conversations remains an open question in `requirements.md`. Persistence of unverified text is outside the agreed current-exchange behavior.

## Scenario-to-test mapping

Use offline provider and retrieval fakes for service coverage. Exercise the exchange route and chat panel for observable delivery behavior. The entries below describe verification targets, including planned tests for S-018 and S-019.

- S-001: scripted draft passes all checks, the answer is returned and saved.
- S-002: relevance fails, the draft is never returned or saved.
- S-003: claim check fails, revised draft is checked and returned.
- S-004: citation check fails, corrected citation (P2) is checked and returned.
- S-005: insufficient evidence, second search adds P2, the final answer cites P1 and P2.
- S-006: retry budget used up, no further retry, final answer cites P1 and states the end date is not established.
- S-007: service test is not needed. Route and chat-panel tests with a controllable clock assert no progress message through five seconds, then the progress message while validation is still pending, and no draft text while validation is pending.
- S-008: controllable clock reaches 30 seconds while a retry waits for evidence. The answer has the verified May start citing P1 and explains the missing end date. An available unchecked draft is not offered.
- S-009: clock reaches 30 seconds before the first check completes and before a generated draft arrives. The answer is the timeout message and the draft is hidden.
- S-010: three off-topic drafts with start and end dates established by checked passages. The answer is the relevance message, with no source-gap claim and no further retry.
- S-011: validator raises before the deadline. The pending exchange is discarded, the error message is returned and the draft is hidden.
- S-012: manuscript text says July 12, the report gives July only. The answer attributes July 12 to the manuscript and says the report leaves the day unverified.
- S-013: validator error at exactly 30 seconds, with and without verified findings when no eligible pending text is available. The deadline response is returned, not the service-error message.
- S-014: directly supported start and end months have the correct citations and use zero generation attempts.
- S-015: one proposal distinguishes the pilot from follow-up activity. Verify the selected excerpts and citations locally.
- S-016: a genuine month excerpt does not verify a proposed year. Repeat retrieval within budget and withhold the unsupported year.
- S-017: a provider failure consumes the single attempt. Verify the interruption response without displaying a draft.
- S-018: a proposal arrives before the deadline. With nothing verified, one pending claim and one rejected claim, verify that JSON and stream delivery allow the panel to offer a collapsed draft. Opening it reveals only the pending claim with an unverified label. Assert one generation attempt.
- S-019: all proposed claims were rejected before the deadline. Verify the timeout message with no draft offer.

Service and provider coverage belongs alongside `test_answer_validation.py`, `test_source_answer_candidates.py` and `test_generation_budget.py`. Delivery coverage belongs in `test_exchange_validation_routes.py`, `chat.spec.js` and `ChatPanel.spec.js`. Follow the test-first dependencies in `tasks.md`.
