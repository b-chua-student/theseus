# Brief: Validate source-backed Assistant answers

- ID: assistant-answer-validation (#125)
- Owner: spatrickjs
- Date: 2026-11-26
- Base SHA: 1dab3f5

## Goal

Give Theseus users answers that address their questions and accurately reflect evidence from the Source Library, by checking each draft answer before presenting it as verified.

## Users / Roles

- Theseus user who asks the Assistant a question answered from the Source Library.

## In Scope

- Check that a draft addresses the question and that its claims and citations are supported by the retrieved passages.
- Use the review to narrow unsupported claims or correct citations.
- When the retrieved passages are insufficient, look for better evidence and check the resulting draft.
- Limit retries per request and explain any evidence gaps that remain.

## Non-Goals

- Offline evaluation runs for maintainers, tracked in `tickets/assistant-answer-evaluation.md`.

## Constraints

- Validate claims before presenting them as findings. Only the deadline fallback may offer unchecked text as an explicitly labeled draft.
- Allow up to two evidence-recovery steps within the validation window. Retrieve missing evidence before review when needed. The review may narrow a claim or correct its citation against the available passages. After review, show only supported findings and explain outstanding gaps; never dispatch another generation attempt.
- Allow 30 seconds for validation and all retries combined, starting when the first draft is ready to check.
- Allow at most two Gemini generation attempts per Source Library exchange: one to draft and one to review. Failures and timeouts consume their attempt. Do not automatically resend either call. Count search embeddings separately.
- Reuse a fully reviewed successful answer and its citations with zero generation attempts only for the exact same question in the same authorized project and conversation, with identical selected sources, retrieved evidence, citation details, relevant conversation inputs and review configuration. Partial answers, errors, timeouts and unverified drafts are ineligible.
- When a successful search returns no passages, explain that the search found insufficient evidence and use zero generation attempts. If retrieval fails, report the interruption instead.

## Known Touchpoints

- Source Library retrieval, answer drafting, Gemini review and citation checks and the citations displayed to the writer.

## Assumptions

- None supplied.

## Open Questions

- Suggestion, not a requirement: should validation apply to answers that do not use the Source Library? Deferred: not covered by the ticket.

## Success Criteria

1. A relevant answer is displayed once its claims and citations pass validation.
2. A draft that fails to address the question is never displayed.
3. An unsupported claim or mismatched citation is corrected, and the revision is checked before it is displayed.
4. When evidence is insufficient and retries remain, the Assistant searches again and checks the resulting draft before display.
5. At the retry limit, the displayed answer states what the sources support and identifies the remaining evidence gaps.
6. If validation is still running after five seconds, show “Checking the answer against your sources…” and keep draft text hidden.
7. At the 30-second deadline, including a simultaneous service error, show verified findings with citations and identify unfinished checks. If nothing was verified and Gemini returned a draft before the deadline, offer “View unverified draft” only for claims still awaiting a check. Hide the draft until selected, label it unverified when opened, and exclude claims already found unsupported or off-topic. If no eligible text remains, say “I couldn’t verify an answer within 30 seconds. Please try again.”
8. If the review finds the entire draft off-topic, say “I couldn’t produce a verified answer to your question.” Describe a source gap only when checked passages establish one.
9. If a service error prevents validation before the deadline, withhold the unchecked draft and say “I couldn’t finish checking this answer. Please try again.”
10. Reuse a fully reviewed successful answer and its citations with zero generation attempts only for the exact same question in the same authorized project and conversation, with identical selected sources, retrieved evidence, citation details, relevant conversation inputs and review configuration. Partial answers, errors, timeouts and unverified drafts are ineligible.
11. For a new question with evidence, Gemini drafts once and separately reviews relevance and factual support against the original question and cited passages. Confirm citation identities before display. A genuine excerpt containing a number does not establish which group it describes.
12. Allow at most two Gemini generation attempts per Source Library exchange: one to draft and one to review. Failures and timeouts consume their attempt. Do not automatically resend either call. Count search embeddings separately.
13. When a successful search returns no passages, explain that the search found insufficient evidence and use zero generation attempts. If retrieval fails, report the interruption instead.

## Reference Links

- Ticket: `tickets/assistant-answer-validation.md`
- Issue: #125
