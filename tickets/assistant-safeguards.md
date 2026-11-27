# [ASSISTANT-SAFEGUARDS-02] As a writer, I can ask questions with chat safeguards active

## Intent
Protect the assistant and its provider quota while preserving ordinary multi-turn conversations.

## Context
Writers ask questions in any assistant scope. Evaluators check direct instruction overrides, instruction disclosure attempts, and bursts of chat questions. This feature complements ASSISTANT-GUARDRAILS-01.

## Scope
- Screen incoming questions for high-confidence direct attempts to override or disclose internal instructions.
- Limit bursts of chat questions and bound the conversation history forwarded with each question.

## Expected Outcomes
- [ ] Both types of direct attempt receive a prompt-injection error before any model call. The rejected question leaves no pending or stored exchange.
- [ ] Benign academic questions discussing prompt injection or system prompts reach the model and receive an answer.
- [ ] With the default burst limit enabled, the first ten ordinary questions in a fresh minute succeed. An eleventh within that minute receives a rate-limit error before any model call for that question.
- [ ] Automated tests can submit the same eleven questions without rate-limit rejection unless they explicitly enable limiting.
- [ ] By default the model receives up to the ten most recent completed exchanges in chronological order. All prior exchanges remain stored.

## Rules / Constraints
The default burst limit is ten chat questions per minute. The default history window is ten completed exchanges.

## Non-Functional Requirements
Automatically verify input blocking, benign pass-through, burst limiting, and history capping without network access or live credentials.

## Out of Scope
Changes to existing system instructions, untrusted-data boundaries, and content safety filters. Post-generation answer validation, semantic embeddings, document chunking, vector storage, background indexing, and document parsing.

## Open Questions
Resolved. All projects use the same limits in this release: ten chat questions per minute when rate limiting is enabled and the ten most recent completed exchanges for model history. Per-project overrides are out of scope.

## Output Paths
Feature directory: `specs/assistant/chat-safeguards/`.

- Intake brief: `brief.md`
- Gherkin: `gherkin.feature`
- Spec files: `requirements.md`, `design.md`, and `tasks.md`

## Definition of Done
- [ ] Intake generated and approved
- [ ] Gherkin generated and approved
- [x] Open questions resolved
- [ ] Spec, Gherkin, and code in sync
- [ ] Reviewed and merged
