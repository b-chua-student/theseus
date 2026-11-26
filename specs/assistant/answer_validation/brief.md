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
- Revise a draft that overstates the evidence or cites a passage that does not support it, then check the revision.
- When the retrieved passages are insufficient, look for better evidence and check the resulting draft.
- Limit retries per request and explain any evidence gaps that remain.

## Non-Goals

- Offline evaluation runs for maintainers, tracked in `tickets/assistant-answer-evaluation.md`.

## Constraints

- Validate claims before presenting them as findings. Only the deadline fallback may offer unchecked text as an explicitly labeled draft.
- Allow two retries after the initial validation. Each retry can revise the draft, retrieve more evidence, or do both. Checking the resulting draft is part of that retry.
- Allow 30 seconds for validation and all retries combined, starting when the first draft is ready to check.
- Use at most one Gemini generation request across the entire source-backed exchange. A failed attempt counts. Track embeddings separately from generation.
- Check every proposed answer locally against the question and the cited passages, including answers proposed by Gemini. Retrieval, local revision and rechecking can continue within the existing retry and time limits.

## Known Touchpoints

- Source Library retrieval, answer drafting, local evidence checks and the citations displayed to the writer.

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
8. If every draft is off-topic and retries are exhausted, say “I couldn’t produce a verified answer to your question.” Describe a source gap only when checked passages establish one.
9. If a service error prevents validation before the deadline, withhold the unchecked draft and say “I couldn’t finish checking this answer. Please try again.”
10. Answer a locally verifiable question with cited evidence and zero generation requests.
11. When local selection is inconclusive, the Assistant may use one generation request to propose an answer with exact excerpts. Verify the claim, excerpt and citation together before presenting a finding. A genuine quote giving the wrong level of detail cannot answer the question.
12. After the generation allowance is spent, correct or narrow the draft locally, retrieve again if appropriate, or return the applicable fallback. The entire exchange stays within the cap even if generation fails.

## Reference Links

- Ticket: `tickets/assistant-answer-validation.md`
- Issue: #125
