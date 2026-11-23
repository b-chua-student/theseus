# Feature intake — Compare a manuscript with selected library sources

Issue #120 · assistant-combined-context

## Goal

A writer can ask which selected sources support a claim in the current draft, or quote a particular passage and ask how the evidence compares. The Assistant uses the draft and evidence from the selected sources in one answer.

## In Scope

- Provide one Context dropdown with Web, Manuscript, individual indexed project sources and All indexed sources. Web is general chat using model knowledge. It provides no live browsing. New chats start on Web.
- Select Web, Manuscript and sources independently. Checking or unchecking Manuscript or a source never changes Web's current setting. Writers can turn Web off to ground an answer in the selected project material alone. Clear selection, or removing the last selected item, returns to Web.
- Keep one conversation across changes. Web alone maps to the existing API scope `none`, including when displaying a saved record with that scope. A combined selection must convey all active choices.
- For a combined question, use the current manuscript text at send time, including unsaved edits. When the writer quotes a passage, carry the exact quote as a separate item from the question text, so the answer addresses that passage. When Manuscript is unchecked, quoting shares only that exact passage from the draft, not the rest of the manuscript, and leaves every context selection unchanged.
- Limit library evidence to the selected sources. Identify the source behind each finding so the writer can tell which sources support, qualify or contradict the claim.

## Non-Goals

Live web browsing and searching sources outside the active project are outside scope.

## Constraints

Source identity follows the library entry ID. The checked sources at send time determine which sources may supply evidence for that exchange. Unselected sources stay excluded even when they contain a closer match.

Checking or unchecking an item takes effect immediately, with no Apply step. Arrow keys move focus between items, Space toggles the focused item, and Escape closes the dropdown and returns focus to the Context button.

Definitions used below:
- Unavailable: a selected source that cannot be searched at send time.
- Searched without a match: a selected source that was searched and has no relevant passage.
- Qualifies: a passage agrees with the claim only under narrower conditions. Contradicts: a passage states a conflicting fact.

## Success Criteria

1. A writer can select Manuscript with one or more individual sources in the same dropdown, include or exclude Web, revise the selection, or clear it to return to Web. Selecting Manuscript or a source keeps Web as it was. The next exchange uses the resulting selection and stays in the same conversation.
2. A combined answer uses the latest draft and evidence from the selected sources together. It identifies which selected sources support or qualify the claim and accurately describes conflicting evidence when present.
3. When a writer quotes a passage, the answer compares that specific passage with evidence from the selected sources, even when the manuscript contains other similar claims. With Manuscript unchecked, only the quoted passage reaches the Assistant and the selection does not change.
4. Library evidence comes only from selected sources in the current project. A source from another project is never used. Manuscript-only, source-only and Web-only selections continue to work.
5. Identify each selected source that could not be checked or yielded no relevant passage. Continue with usable selected evidence. If none is usable, say the claim could not be verified from the selection. Missing evidence alone cannot establish a contradiction. With Web enabled, distinguish general knowledge from findings attributed to selected sources.
6. Keep Web, Manuscript and the Clear selection action visible while the source list scrolls. Filter sources by title without clearing checked items. Summarize the selection on the closed button, for example **Manuscript + 2 sources**.

7. All indexed sources checks every indexed source currently in the project, including entries hidden by a title filter. It preserves Web and Manuscript. Unchecking one source retains the others and clears the all-selected indicator. Checking every source restores the indicator. Disable this option when no sources are indexed.

## Decisions

- **Relevance and source coverage.** Attempt to search every selected source. A passage is relevant when it provides evidence that supports, qualifies or contradicts the specific claim or quoted passage. Each source gets a chance to contribute, with no fixed quota of passages per source. Report “no relevant passage” only after a completed search. If a source could not be searched, identify it as unavailable. Set the numerical relevance threshold and passage budget during design and testing.
- **Saved conversations.** Reopening a chat restores the Web and Manuscript settings and the source selection from its last successful exchange. If a saved source has become unavailable, identify it by name and preserve the remaining choices. New chats start on Web.
- **Large selections.** All indexed sources selects the entire indexed library in the active project at the time of selection, including titles hidden by a filter. Use that set for the exchange, subject to the writer’s later changes. Newly indexed sources are included only if the writer selects them. Support selections larger than the current 1,000-ID request limit without silent truncation. If any selected sources cannot be checked, identify them in the result. Batching and request representation are design decisions.
