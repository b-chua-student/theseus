# Assistant feedback on Source Library evidence

Ready for review · [Issue #127](https://github.com/b-chua-student/theseus/issues/127)

## Goal

A user reading a Source Library answer can tell whether the Assistant used relevant library evidence to produce that answer.

## In Scope

Show evidence-use feedback with each Source Library answer. The feedback reflects what the Assistant actually used. A search that returns a passage is insufficient on its own to indicate that the answer used evidence.

Source Library answers only. Answers in the manuscript or no-context scopes show no evidence-use feedback.

## Non-Goals

- Explaining why no library evidence was used (no relevant results, sources still indexing, or a retrieval failure).

## Constraints

The issue specifies no required wording, visual treatment, or non-functional requirements.

- The feedback is available for new answers and for answers in a reopened conversation.
- Answers created before this feature have no evidence-use record and show no feedback.

## Success Criteria

1. When an answer draws on relevant library evidence, the user can tell from that answer that library evidence was used.
2. When the Assistant answers without relevant library evidence, the answer clearly states that it was generated without library evidence. This applies even if a search returned passages that the Assistant did not use, and when the search fails.
3. Answers outside the Source Library do not show evidence-use feedback.

## Decisions

Evidence-use feedback reports only whether library evidence was used. It does not explain why none was used.

## Follow-up

Reason-specific wording (no relevant results, sources still indexing, retrieval failure) awaits a product decision and is out of scope for this issue.
