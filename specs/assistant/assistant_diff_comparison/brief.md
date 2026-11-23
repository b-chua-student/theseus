# Intake brief — Explain changes between saved revisions

Draft for review · [Issue #126](https://github.com/b-chua-student/theseus/issues/126)

## User story

As an Assistant user, I want to ask what changed between two saved revisions so I can understand the edits in plain language.

## Scope and dependency

The user selects a pair of saved revisions of one draft and asks the Assistant a question about their differences. A pair is identified by the manuscript, the draft, and two revision IDs. The first selected revision is the starting revision and the second is the ending revision. The Assistant describes changes from the starting revision to the ending revision.

The Assistant uses the comparison from the [revision diff engine (#119)](https://github.com/b-chua-student/theseus/issues/119). That engine does not exist yet. The Assistant context reaches it through a new port (for example `RevisionDiffProvider`) and must not import `revision_history` services directly. Until #119 lands, the Assistant side is built and tested against an in-memory fake of that port.

## Acceptance criterion 1

Given two selected saved revisions, the user can ask what changed and receive an answer grounded in that comparison.

- The answer gives old and new values in that order. For example, if a deadline moved from Friday to Monday, the answer says Friday first, then Monday. The order follows the selection, so a reversed pair reverses the description.
- A change introduced after the selected pair falls outside the answer.
- If the comparison contains no differences in snapshot content, the answer tells the user that directly. Differences in revision message or timestamp alone do not count.
- A question about one detail is answered from that detail, without listing unrelated changes.
- Revision text is treated as document text, never as instructions to the Assistant.

## Acceptance criterion 2

The Assistant refuses to answer, with a clear message, when the selection is invalid:

- either revision does not exist
- only one revision is selected, or the same revision is selected twice
- the revisions belong to different drafts
- the revisions belong to a project the user cannot access

## Acceptance criterion 3

If the comparison is larger than the Assistant can take as context, the user is told the comparison is too large instead of receiving a partial answer presented as complete. The limit is set during design and must not exceed the existing manuscript context cap (500,000 characters).

## Out of scope for now

Unsaved changes and comparisons across drafts are not supported. A cross-draft pair is rejected (criterion 2). Revisit this if review decides otherwise.
