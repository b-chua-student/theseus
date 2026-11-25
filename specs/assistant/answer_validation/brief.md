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

- Check every draft, including revisions, against the writer's question and the retrieved evidence before display.
- Bound retries for each request.

## Known Touchpoints

- Assistant answers, Source Library passages, and citations.

## Assumptions

- No additional assumptions.

## Open Questions

- Retry count, how different retry types share the allowance, and acceptable wait time — Deferred: product decision needed.
- Whether to show progress while checking an answer — Deferred: product decision needed.
- Message or error when every draft is off-topic and retries are exhausted — Deferred: product decision needed.
- How should the Assistant communicate a service error that prevents validation, and what recovery should it offer? — Deferred: product decision needed.
- Intake owner — Deferred: assignment has not been confirmed in the supplied ticket.

## Success Criteria

1. Show a relevant answer whose claims are supported by the retrieved passages it cites.
2. Withhold off-topic or unsupported drafts from display. Check any replacement before showing it.
3. Correct overstatements and mismatched citations. Distinguish missing support from contradictory evidence.
4. When evidence is insufficient and a retry is available, search again and check the resulting answer.
5. Stop at the request's retry limit and report the supported findings and remaining evidence gaps.

## Reference Links

- [Answer validation ticket #125](https://github.com/b-chua-student/theseus/issues/125)
- [Combined-context ticket #120](https://github.com/b-chua-student/theseus/issues/120)
