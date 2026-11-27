# [assistant-answer-validation] As a Theseus user, I can receive answers checked against source evidence

## Intent

Check each draft answer to a source-backed question before presenting it as a verified answer.

## Context

The Assistant retrieves passages from the Source Library to answer questions. This ticket covers checks that happen during each request.

## Scope

- Check that the draft addresses the question and that its claims and citations are supported by the retrieved passages.
- Gather additional evidence when needed and use the review to correct or withhold unsupported findings.
- Limit retries and explain any evidence gaps that remain.

## Expected Outcomes

- [ ] A draft that answers the question and uses supporting evidence can be shown to the user.
- [ ] Each displayed finding and any corrected citation are supported by the review.
- [ ] When the retry limit is reached, the Assistant explains what the available sources support and where the evidence falls short.

## Rules / Constraints

- Validate claims before presenting them as findings. Only the deadline fallback may offer unchecked text as an explicitly labeled draft.
- Allow up to two evidence-recovery steps within the validation window. Retrieve missing evidence before review when needed. The review may narrow a claim or correct its citation against the available passages. After review, show only supported findings and explain outstanding gaps; never dispatch another generation attempt.
- If validation is still running after five seconds, show “Checking the answer against your sources…” and keep draft text hidden.
- If the review finds the entire draft off-topic, say “I couldn’t produce a verified answer to your question.” Describe a source gap only when checked passages establish one.
- If a service error prevents validation before the deadline, withhold the unchecked draft and say “I couldn’t finish checking this answer. Please try again.”

## Non-Functional Requirements

- Allow 30 seconds for validation and all retries combined, starting when the first draft is ready to check.
- At the 30-second deadline, including a simultaneous service error, show verified findings with citations and identify unfinished checks. If nothing was verified and Gemini returned a draft before the deadline, offer “View unverified draft” only for claims still awaiting a check. Hide the draft until selected, label it unverified when opened, and exclude claims already found unsupported or off-topic. If no eligible text remains, say “I couldn’t verify an answer within 30 seconds. Please try again.”
- Allow at most two Gemini generation attempts per Source Library exchange: one to draft and one to review. Failures and timeouts consume their attempt. Do not automatically resend either call. Count search embeddings separately.
- Reuse a fully reviewed successful answer and its citations with zero generation attempts only for the exact same question in the same authorized project and conversation, with identical selected sources, retrieved evidence, citation details, relevant conversation inputs and review configuration. Partial answers, errors, timeouts and unverified drafts are ineligible.
- When a successful search returns no passages, explain that the search found insufficient evidence and use zero generation attempts. If retrieval fails, report the interruption instead.
- For a new question with evidence, Gemini drafts once and separately reviews relevance and factual support against the original question and cited passages. Confirm citation identities before display. A genuine excerpt containing a number does not establish which group it describes.

## Out of Scope

- Offline evaluation runs for maintainers, tracked in `tickets/assistant-answer-evaluation.md`.

## Open Questions

The retry, timing, and progress decisions are recorded above. No open questions remain for source-backed validation.

## Output Paths

- Intake brief: `specs/assistant/answer_validation/brief.md`
- Gherkin: `specs/assistant/answer_validation/gherkin.feature`
- Spec files: `requirements.md`, `design.md`, and `tasks.md` in `specs/assistant/answer_validation/`.

Use scenario IDs S-098 through S-120 for answer-validation coverage so they stay unique within the Assistant context.

## Definition of Done

- [ ] Intake generated and approved
- [ ] Gherkin generated and approved
- [ ] Open questions resolved
- [ ] Spec, Gherkin, and code in sync
- [ ] Reviewed and merged
