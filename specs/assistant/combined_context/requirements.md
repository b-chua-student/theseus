# Requirements - Compare a manuscript with selected library sources

- Source: `specs/assistant/combined_context/brief.md` (issue #120). No ticket file is kept for this feature.

## Requirements

Each requirement comes from the intake's goal, in-scope items, constraints, success criteria or decisions. The Ticket lines column is `-` because there is no ticket file.

| ID | Requirement | Source | Ticket lines | Scenarios |
| --- | --- | --- | --- | --- |
| R-001 | One Context dropdown offers Web, Manuscript and individual indexed project sources. A new chat starts on Web, which is general chat from model knowledge with no live browsing, and Web alone uses the existing API scope `none`. A writer can combine Manuscript with one or more sources, include or exclude Web, and revise the selection. Checking or unchecking Manuscript or a source leaves Web as it was. Unchecking the last checked item, or choosing Clear selection, leaves only Web checked. | from intake | - | S-063, S-065, S-066, S-080, S-086, S-087 |
| R-002 | A change to the selection takes effect immediately, with no Apply step. The next exchange uses the resulting selection and stays in the same conversation. | from intake | - | S-064, S-076 |
| R-003 | A combined question uses the manuscript text as it reads at send time, including unsaved edits. Manuscript-only, source-only and Web-only selections continue to work and share only the context they select. | from intake | - | S-067, S-070 |
| R-004 | A combined answer uses the latest draft and evidence from the selected sources together. It identifies the source behind each finding, which selected sources support or qualify the claim, and accurately describes conflicting evidence. | from intake | - | S-068, S-078 |
| R-005 | A writer can quote a passage. The exact quote travels as its own item, separate from the question text, and the answer compares that passage with the selected sources, even when the manuscript has other similar claims. With Manuscript unchecked, only the quoted passage is shared and the selection does not change. | from intake | - | S-069, S-075, S-088, S-089 |
| R-006 | Library evidence comes only from the sources checked at send time in the current project. Unselected sources and sources from another project are never searched or used, even when they contain a closer match. With Web off, factual findings come only from the manuscript and the selected sources. | from intake | - | S-068, S-077, S-084 |
| R-007 | The answer identifies each selected source that could not be checked (unavailable) or had no relevant passage (searched without a match), and continues with the usable evidence. If none is usable, it says the claim could not be verified from the selection. Missing evidence alone never establishes a contradiction. With Web enabled, general knowledge is distinguished from findings attributed to selected sources. | from intake | - | S-072, S-073, S-079, S-085 |
| R-008 | Every selected source is searched. Passages are ranked by cosine similarity, and only those at or above the configured relevance threshold are eligible. A source with many matches cannot crowd out another selected source, and a search that completes with no eligible passage is reported as searched without a match. | from intake | - | S-094, S-095 |
| R-009 | The Context dropdown is operable by keyboard: arrow keys move focus, Space toggles the focused item, and Escape closes it and returns focus to the Context button. Web, Manuscript and Clear selection stay visible while the source list scrolls. Filtering by title keeps checked items checked. The closed button summarizes the selection, for example "Manuscript + 2 sources". | from intake | - | S-071, S-074 |
| R-010 | "All indexed sources" is the only bulk checkbox. It checks every indexed source in the project at that moment, including entries hidden by the title filter, and preserves Web and Manuscript. Unchecking one source clears the all-selected indicator and checking every source restores it. The option is disabled when no sources are indexed. Sources indexed afterward are included only if the writer selects them. | from intake | - | S-081, S-082, S-083, S-093 |
| R-011 | A selection larger than the current 1,000-ID request limit is searched in full. No selected source is silently dropped, and one that cannot be searched is reported as unavailable. Evidence fits the model's available context window. Each source whose relevant evidence was omitted for capacity is named, and only library evidence supplied to the model is cited. | from intake | - | S-092, S-096 |
| R-012 | Reopening a saved chat restores the Web and Manuscript settings and the source selection from its last successful exchange. A saved record with scope `none` shows as Web alone. A saved source that is no longer available is named and the remaining choices stay checked. | from intake | - | S-090, S-091 |

## Open Questions

- The intake does not say how a legacy saved record with scope `manuscript` or `source_library` should appear when reopened. D-006 proposes Manuscript alone and the saved sources, each with Web off. Confirm this mapping (T-002).
- The relevance threshold and the passage budget have no values yet. The intake leaves them to calibration on labelled passages and to design and testing (D-007, T-009).
