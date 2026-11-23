# Feature intake — Compare a manuscript with selected library sources

Issue #120 · assistant-combined-context

## Goal

A writer can ask which selected sources support a claim in the current draft, or quote a particular passage and ask how the evidence compares. The Assistant uses the draft and evidence from the selected sources in one answer.

## In Scope

- Provide one Context dropdown that replaces the current None / Manuscript / Source Library buttons and the separate source picker. Manuscript and each indexed source in the current project's Source Library can be checked independently. The writer can select one or more sources alongside Manuscript.
- Selecting another source adds it to the selection. Unchecking a source removes just that source. None clears all selections. Removing the last selected item also selects None, so an empty selection never exists.
- Keep the existing ways to ask with Manuscript alone, selected sources alone, or None. The writer can change context within a conversation, and changing it never starts a new conversation.
- For a combined question, use the current manuscript text at send time, including unsaved edits. When the writer quotes a passage, carry the exact quote as a separate item from the question text, so the answer addresses that passage.
- Limit library evidence to the selected sources. Identify the source behind each finding so the writer can tell which sources support, qualify or contradict the claim.

## Non-Goals

The one-click Select all shortcut is deferred for this version. Writers choose sources individually.

## Constraints

Source identity follows the library entry ID. The checked sources at send time determine which sources may supply evidence for that exchange. Unselected sources stay excluded even when they contain a closer match.

Checking or unchecking an item takes effect immediately, with no Apply step. Arrow keys move focus between items, Space toggles the focused item, and Escape closes the dropdown and returns focus to the Context button.

Definitions used below:
- Unavailable: a selected source that cannot be searched at send time.
- Searched without a match: a selected source that was searched and has no relevant passage.
- Qualifies: a passage agrees with the claim only under narrower conditions. Contradicts: a passage states a conflicting fact.

## Success Criteria

1. A writer can select Manuscript with one or more individual sources in the same dropdown, revise the selection, or clear it. The next exchange uses the resulting selection and stays in the same conversation.
2. A combined answer uses the latest draft and evidence from the selected sources together. It identifies which selected sources support or qualify the claim and accurately describes conflicting evidence when present.
3. When a writer quotes a passage, the answer compares that specific passage with evidence from the selected sources, even when the manuscript contains other similar claims.
4. Library evidence comes only from selected sources in the current project. A source from another project is never used. Manuscript-only, source-only and None selections continue to work.
5. Identify each selected source that could not be checked or yielded no relevant passage. Continue with usable selected evidence. If none is usable, say the claim could not be verified from the selection. Missing evidence alone cannot establish a contradiction.
6. Keep Manuscript and None visible while the source list scrolls. Filter sources by title without clearing checked items. Summarize the selection on the closed button, for example **Manuscript + 2 sources**.

## Open Decisions

Product choices not yet made. They do not change the scenarios above but must be settled before build:
- What makes a passage relevant enough to count as a match, and whether each selected source gets a guaranteed share of retrieved passages.
- Whether a saved conversation restores its selection, including Manuscript.
- Whether the current "All library sources" option is removed. Select all is deferred, so removal is assumed.
- The maximum number of sources selectable at once.
