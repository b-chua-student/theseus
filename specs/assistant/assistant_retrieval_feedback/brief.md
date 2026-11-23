# Assistant feedback on Source Library evidence

Draft for review · [Issue #127](https://github.com/b-chua-student/theseus/issues/127)

## Goal

A user reading a Source Library answer can tell whether the Assistant used relevant library evidence to produce that answer.

## In Scope

Show evidence-use feedback with each Source Library answer. The feedback reflects what the Assistant actually used. A search that returns a passage is insufficient on its own to indicate that the answer used evidence.

## Non-Goals

The issue specifies no explicit exclusions.

## Constraints

The issue specifies no required wording, visual treatment, or non-functional requirements.

## Success Criteria

- When an answer draws on relevant library evidence, the user can tell from that answer that library evidence was used.
- When the Assistant answers without relevant library evidence, the answer clearly states that it was generated without library evidence. This applies even if a search returned passages that the Assistant did not use.

## Open Question

Should the feedback explain why an answer used no library evidence, distinguishing a search with no relevant results, sources still indexing, and a retrieval failure? The scenarios cover the evidence-use status whenever an answer is produced. Reason-specific wording awaits a product decision.
