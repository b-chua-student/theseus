# Feature intake — Compare a manuscript with selected library sources

Issue [#120][ticket] · assistant-combined-context · Original Markdown body, lines numbered including blanks, verified 24 Nov 2026. `from ticket` marks an explicit outcome or constraint. `assumed` marks a detail supplied outside the issue body. For an adopted clarification, the citation identifies the lead’s decision or the author’s recorded interpretation. Unconfirmed suggestions are listed under Open Questions.

## Goal

`from ticket` A writer can check a manuscript claim or quoted passage against selected library sources in one Assistant answer. [Intent L5; Expected Outcomes L18–19][ticket]

## In Scope

- `from ticket` Compare the current manuscript, including unsaved edits, with selected sources. Support questions about a specific quoted passage. [Scope L13–14][ticket]
- `assumed` Keep the bulk-selection option in the Context dropdown as **All indexed sources** and use **Web** as the general-chat label. The ticket asked about bulk selection and described the prior context modes. [Context L9; Open Questions L35][ticket] · [Lead’s selection and naming decision][review] · [Author’s dropdown clarification][filter]
- `assumed` Explain evidence gaps for each selected source. [Open Questions L36][ticket] · [Lead’s answer][review]

## Non-Goals

`from ticket` The issue lists no explicit exclusions. [Out of Scope L29–31][ticket]

`assumed` Web denotes the existing general-chat mode. Live browsing is outside this change. [Context L9][ticket] · [Lead’s naming decision][web] · [Author’s API clarification][fallback]

## Constraints

`from ticket` Use only library evidence from the sources the writer selected, even when an unselected source has a closer match. [Rules / Constraints L23][ticket]

## Success Criteria

1. `from ticket` Use the writer’s chosen sources and manuscript together. [Scope L13; Expected Outcomes L18][ticket] **Review clarifications** (`assumed`): clearing the selection or its last item returns to Web. Reopening restores Web, Manuscript and sources from the last successful exchange. Name an unavailable saved source and retain the remaining choices. [Context L9; Scope L13][ticket] · [Author’s fallback rule][fallback] · [Lead’s restore decision][restore] · [Author’s restoration detail][restore-detail]
2. `from ticket` Use the current draft, including unsaved edits, and identify which selected sources support the claim. A comparison can show agreement, a narrower finding, or conflicting evidence. [Scope L13; Expected Outcomes L18–19][ticket]
3. `from ticket` Address the selected manuscript passage in the answer and compare that passage with evidence from the chosen sources. [Scope L14; Expected Outcomes L19][ticket]
4. `from ticket` Only selected sources may contribute library evidence. [Rules / Constraints L23][ticket] `assumed` Preserve the standalone contexts and the current project boundary. Web-only chat supplies no project material and uses the existing API scope `none`. [Context L9][ticket] · [Author’s compatibility clarification][fallback] · [Existing project-scoped retrieval][retrieval]
5. `assumed` Name each unavailable source or completed search without a relevant passage. Continue with usable selected evidence. If none is usable, say the claim could not be verified from the selection. General knowledge and missing evidence cannot establish what a selected source supports. [Expected Outcomes L18; Rules L23; Open Questions L36][ticket] · [Lead’s evidence-gap decision][review]
6. `assumed` With a title filter active, **All indexed sources** includes sources hidden by the filter. Other large-library UI details are proposals under Q2. [Open Questions L35][ticket] · [Author’s filter clarification][filter]
7. `assumed` Offer **All indexed sources** in this release. Source count does not limit selection. Attempt to search the selected set and fit evidence within the model’s context window. Name a matching source whose evidence could not fit. [Rules L23; Open Questions L35–36][ticket] · [Lead’s bulk-selection decision][bulk] · [Lead retained the existing option][retain] · [Lead’s capacity decision][capacity] · [Author’s capacity clarification][capacity-detail]

## Decisions

- `assumed` For criterion 5, rank passages by cosine similarity between the query and passage embeddings. Only passages meeting the configured cutoff are eligible. A completed search below cutoff has no match. A failed search is unavailable. Calibrate the cutoff during implementation using examples that include contradictory passages. [Rules L23; Open Questions L36][ticket] · [Lead’s scoring guidance][cosine] · [Lead’s threshold review][threshold] · [Author’s calibration plan][calibrate]
- `assumed` For criterion 7, passage capacity depends on space left after instructions, conversation history, the question, any included quote or manuscript, and room for the response. The 1,001-source scenario exercises the existing API boundary. [Open Questions L35][ticket] · [Lead’s capacity decision][capacity] · [Author’s explanation of evidence budgeting][capacity-detail]

## Open Questions

The following proposals appeared in the working drafts. Record a ticket or review decision before treating them as release criteria. The feature file retains their original scenario IDs as candidate examples.

- `assumed` **Q1 — Context controls.** Should Web start checked, toggle independently in either direction, and allow an answer grounded only in selected project material? Should source/context changes apply immediately and always retain the same thread? [Context L9; Scope L13][ticket] · [Lead suggested combining contexts][review]
- `assumed` **Q2 — Library navigation.** Should the menu support arrow keys, Space and Escape, pinned controls, a scrollable title search with persistent individual selections, and a count in the collapsed label? [Scope L13; Open Questions L35][ticket] · [Filter behavior already recorded for bulk selection][filter]
- `assumed` **Q3 — Quotes.** Should the exchange carry an exact quote separately from the question? With Manuscript unchecked, should quoting share only that passage and preserve all selections? [Scope L14; Expected Outcomes L19][ticket]
- `assumed` **Q4 — Bulk selection details.** Should the all-selected indicator track individual toggles, be disabled for an empty library, and snapshot the indexed set so later additions require explicit selection? [Rules L23; Open Questions L35][ticket] · [Lead retained the bulk option][bulk]
- `assumed` **Q5 — Retrieval and reporting.** Should competing sources have a guaranteed chance to contribute passages within budget, and should per-source statuses be passed to the model or rendered by the application? Should chat display a match percentage? The lead requested investigation and the author recommended keeping scores internal. [Expected Outcomes L18; Open Questions L36][ticket] · [Lead’s scoring guidance][cosine] · [Percentage investigation][percent] · [Author’s recommendation][internal]

[ticket]: https://github.com/b-chua-student/theseus/issues/120
[review]: https://github.com/b-chua-student/theseus/pull/141#issuecomment-7097490735
[bulk]: https://github.com/b-chua-student/theseus/pull/141#discussion_r4664301954
[retain]: https://github.com/b-chua-student/theseus/pull/141#discussion_r4664378327
[web]: https://github.com/b-chua-student/theseus/pull/141#discussion_r4664342292
[fallback]: https://github.com/b-chua-student/theseus/pull/141#discussion_r4674711875
[restore]: https://github.com/b-chua-student/theseus/pull/141#discussion_r4664376280
[restore-detail]: https://github.com/b-chua-student/theseus/pull/141#discussion_r4674869655
[filter]: https://github.com/b-chua-student/theseus/pull/141#discussion_r4675025374
[capacity]: https://github.com/b-chua-student/theseus/pull/141#discussion_r4664394567
[capacity-detail]: https://github.com/b-chua-student/theseus/pull/141#discussion_r4675277948
[cosine]: https://github.com/b-chua-student/theseus/pull/141#discussion_r4664375104
[threshold]: https://github.com/b-chua-student/theseus/pull/141#discussion_r4664421731
[calibrate]: https://github.com/b-chua-student/theseus/pull/141#discussion_r4674819214
[percent]: https://github.com/b-chua-student/theseus/pull/141#discussion_r4664446484
[internal]: https://github.com/b-chua-student/theseus/pull/141#discussion_r4675560888
[retrieval]: ../../../backend/domain/assistant/services/chat.py
