# [assistant-answer-validation] As a Theseus user, I can receive answers checked against source evidence

## Intent

Check each draft answer to a source-backed question before showing it to the user.

## Context

The Assistant retrieves passages from the Source Library to answer questions. This ticket covers checks that happen during each request.

## Scope

- Check that the draft addresses the question and that its claims and citations are supported by the retrieved passages.
- When the draft overstates the evidence, revise it and check it again. When the retrieved passages are insufficient, look for better evidence and check the resulting draft.
- Limit retries and explain any evidence gaps that remain.

## Expected Outcomes

- [ ] A draft that answers the question and uses supporting evidence can be shown to the user.
- [ ] When a draft contains an unsupported claim or cites a passage that does not support it, the Assistant revises the draft or retrieves more evidence and checks the answer again before showing it.
- [ ] When the retry limit is reached, the Assistant explains what the available sources support and where the evidence falls short.

## Rules / Constraints

- Validate source-backed answers before showing them to the user.
- Allow two retries after the initial validation. Each retry can revise the draft, retrieve more evidence, or do both. Checking the resulting draft is part of that retry.
- If validation is still running after five seconds, show “Checking the answer against your sources…” and keep draft text hidden.
- If every draft is off-topic and retries are exhausted, say “I couldn’t produce a verified answer to your question.” Describe a source gap only when checked passages establish one.
- If a service error prevents validation, withhold the unchecked draft and say “I couldn’t finish checking this answer. Please try again.”

## Non-Functional Requirements

- Allow 30 seconds for validation and all retries combined, starting when the first draft is ready to check.
- At the deadline, show any validated findings and explain remaining evidence gaps. If no validation completed, tell the user the answer could not be checked.

## Out of Scope

- Offline evaluation runs for maintainers, tracked in `tickets/assistant-answer-evaluation.md`.

## Open Questions

The retry, timing, and progress decisions are recorded above. No open questions remain for source-backed validation.

## Output Paths

- Intake brief: `specs/assistant/answer_validation/brief.md`
- Gherkin: `specs/assistant/answer_validation/gherkin.feature`
- Spec files: `requirements.md`, `design.md`, and `tasks.md` in `specs/assistant/answer_validation/`.

## Definition of Done

- [ ] Intake generated and approved
- [ ] Gherkin generated and approved
- [ ] Open questions resolved
- [ ] Spec, Gherkin, and code in sync
- [ ] Reviewed and merged
