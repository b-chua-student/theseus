# Feature intake — Compare a manuscript with selected library sources

Issue #120 · assistant-combined-context

## Goal

A writer can ask which selected sources support a claim in the current draft, or quote a particular passage and ask how the evidence compares. The Assistant uses the draft and evidence from the selected sources in one answer.

## In Scope

- Provide one Context dropdown with Web, Manuscript and individual indexed project sources. Retain the existing “All library sources” option in this release as a single checkbox labelled **All indexed sources** inside the dropdown. Web is general chat using model knowledge. It provides no live browsing. New chats start on Web.
- Writers can turn Web off to ground an answer in selected project material alone. Checking or unchecking Manuscript or a source preserves Web’s current setting as long as at least one context remains selected. If the writer unchecks the last active context or chooses Clear selection, only Web is selected.
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
- Matched but omitted for capacity: the search found relevant evidence in the source, but none of its relevant passages fit in the available evidence budget.
- Qualifies: a passage agrees with the claim only under narrower conditions. Contradicts: a passage states a conflicting fact.

## Success Criteria

1. A writer can select Manuscript with one or more individual sources in the same dropdown, include or exclude Web, revise the selection, or clear it to return to Web. Selecting Manuscript or a source keeps Web as it was. The next exchange uses the resulting selection and stays in the same conversation.
2. A combined answer uses the latest draft and evidence from the selected sources together. It identifies which selected sources support or qualify the claim and accurately describes conflicting evidence when present.
3. When a writer quotes a passage, the answer compares that specific passage with evidence from the selected sources, even when the manuscript contains other similar claims. With Manuscript unchecked, only the quoted passage reaches the Assistant and the selection does not change.
4. Library evidence comes only from selected sources in the current project. A source from another project is never used. Manuscript-only, source-only and Web-only selections continue to work.
5. Identify each selected source that could not be checked or yielded no relevant passage. Continue with usable selected evidence. If none is usable, say the claim could not be verified from the selection. Missing evidence alone cannot establish a contradiction. With Web enabled, distinguish general knowledge from findings attributed to selected sources.
6. Keep Web, Manuscript and the Clear selection action visible while the source list scrolls. Filter sources by title without clearing checked items. Summarize the selection on the closed button, for example **Manuscript + 2 sources**.

7. All indexed sources checks every indexed source currently in the project, including entries hidden by a title filter. It preserves Web and Manuscript. Unchecking one source retains the others and clears the all-selected indicator. Checking every source restores the indicator. Disable this option when no sources are indexed. When the context window cannot fit evidence from every matching source, name each source whose evidence was omitted for capacity. Only cite library evidence that was supplied to the model.

## Decisions

- **Relevance and source coverage.** Attempt to search every selected source. Rank its passages by cosine similarity between the query embedding and each passage embedding. Only passages scoring at or above the configured relevance threshold are eligible for inclusion. Each source gets a chance to contribute, with no fixed passage quota. If a search completes and no passage meets the threshold, mark that source “searched without a match.” If the search fails, mark it unavailable. During implementation, calibrate the cutoff using representative queries and passages labelled as supporting, qualifying, contradicting or unrelated to the claim. Set the passage budget during design and testing.
- **Saved conversations.** Reopening a chat restores the Web and Manuscript settings and the source selection from its last successful exchange. If a saved source has become unavailable, identify it by name and preserve the remaining choices. New chats start on Web.
- **Large selections.** All indexed sources selects the entire indexed library in the active project at the time of selection, including titles hidden by a filter. Use that set for the exchange, subject to the writer’s later changes. Newly indexed sources are included only if the writer selects them. Attempt to search every selected source, including selections larger than the current 1,000-ID request limit. For each answer, fit retrieved evidence into the model’s available context window after accounting for instructions, conversation history, the question, any quote or selected manuscript text, and room for the response. If a source could not be searched, identify it as unavailable. Batching and request representation are design decisions.
