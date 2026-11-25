# Brief: Validate source-backed Assistant answers

- ID: #125
- Owner: Unconfirmed
- Date: 2026-11-25
- Base SHA: `f53bbb5`

## Goal

Give writers an answer that addresses their question and accurately represents the evidence retrieved from their selected library sources.

## Users / Roles

- A Theseus writer asking the Assistant a source-backed question.

## In Scope

- Check the draft answer against the question, the retrieved passages, and the passages cited for individual claims.
- Revise misleading claims and citations. Search again when more evidence is needed, then check the resulting answer before showing it.
- Explain what the available evidence supports and where it falls short when retries are exhausted.

## Non-Goals

- Offline evaluation runs for maintainers, tracked separately under assistant answer evaluation.
- Applying source validation to a question asked without library sources.

## Constraints

- Keep the writer's original question, selected sources, and manuscript or quote boundaries throughout the request.
- Bound retries for each request. Withheld drafts stay out of the displayed answer and saved conversation.
- If validation fails to complete because of a service error, tell the writer and allow them to ask again.

## Known Touchpoints

- Assistant answers, Source Library passages and citations, and saved conversations.

## Assumptions

- The existing intake treats failure to finish validation and exhaustion of retries as separate outcomes.

## Open Questions

- Retry count, how different retry types share the allowance, and acceptable wait time — Deferred: product decision needed.
- Whether to show progress while checking an answer — Deferred: product decision needed.
- Message or error when every draft is off-topic and retries are exhausted — Deferred: product decision needed.
- Intake owner — Deferred: assignment has not been confirmed in the supplied ticket.

## Success Criteria

1. Show a relevant answer whose claims are supported by the retrieved passages it cites.
2. Withhold off-topic or unsupported drafts from display and history. Check any replacement before showing it.
3. Correct overstatements and mismatched citations. Distinguish missing support from contradictory evidence.
4. When evidence is insufficient and a retry is available, search again within the original selection and check the resulting answer.
5. Stop at the request's retry limit and report the supported findings and remaining evidence gaps.
6. If validation cannot complete because of a service error, show an error and allow another request.
7. Questions asked without library sources continue without source validation.

## Reference Links

- [Answer validation ticket #125](https://github.com/b-chua-student/theseus/issues/125)
- [Combined-context ticket #120](https://github.com/b-chua-student/theseus/issues/120)
