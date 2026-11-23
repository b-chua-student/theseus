# Intake brief — Explain changes between saved revisions

Draft for review · [Issue #126](https://github.com/b-chua-student/theseus/issues/126)

## User story

As an Assistant user, I want to ask what changed between two saved revisions so I can understand the edits in plain language.

## Scope and dependency

The user selects a pair of saved revisions and asks the Assistant a question about their differences. The Assistant uses the comparison from the [revision diff engine (#119)](https://github.com/b-chua-student/theseus/issues/119). It describes changes from the starting revision to the revision being compared with it.

## Acceptance criterion 1

Given two selected saved revisions, the user can ask what changed and receive an answer grounded in that comparison. For example, if a deadline moved from Friday to Monday, the answer gives the old and new days in that order. A change introduced after the selected pair falls outside the answer. If the comparison contains no differences, the answer tells the user that directly.

## Open scope decision

Should the Assistant also explain unsaved changes or support comparisons across drafts? Pending review, the acceptance scenarios cover saved revisions of one draft.
