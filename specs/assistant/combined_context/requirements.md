# Requirements — Compare a manuscript with selected library sources

- Ticket: `tickets/assistant-combined-context.md`

## Requirements

| ID | Requirement | Source | Ticket lines | Scenarios |
| --- | --- | --- | --- | --- |
| R-001 | A writer can select library sources together with the current manuscript and ask one question about both. | from ticket | 13, 18 | S-063, S-064, S-076, S-084 |
| R-002 | A combined question uses the current manuscript, including unsaved edits. | from ticket | 5, 13 | S-067, S-070 |
| R-003 | The answer identifies which selected sources support a manuscript claim, using the manuscript and evidence from the selected sources together, without the writer restating the claim in the question. | from ticket | 18 | S-068, S-078 |
| R-004 | A writer can quote a selected passage and receive a comparison that addresses that passage using evidence from the selected sources. When Manuscript is unchecked, only the quoted passage is shared and the selection does not change. | from ticket | 14, 19 | S-069, S-075, S-088, S-089 |
| R-005 | Only the sources the writer selected may supply library evidence. | from ticket | 23 | S-068, S-070, S-072, S-073, S-077 |
| R-006 | "All indexed sources" is the only bulk-selection checkbox. It selects a snapshot of every indexed library entry in the active project, including entries hidden by the title filter, and preserves Web and Manuscript. Its indicator shows whether all indexed entries are checked, and it is disabled when no source is indexed. Sources indexed later stay unchecked until selected. | from ticket | 39 | S-081, S-082, S-083, S-093 |
| R-007 | Name each selected source that could not be searched (unavailable), was searched without a match, or had relevant evidence omitted for capacity. Continue with the usable evidence. If none is usable, report that the claim could not be verified from the selection. A contradiction requires conflicting evidence. When Web is enabled, distinguish general knowledge from library findings. | from ticket | 40 | S-072, S-073, S-079, S-085, S-096, S-097 |
| R-008 | Attempt every selected project source, including selections above 1,000. Admit passages at or above the calibrated cosine cutoff. Give each matching source a chance to contribute a fitting passage before taking more from another source. Calculate the available space for each exchange and cite only supplied evidence. | from ticket | 24 | S-092, S-094, S-095, S-096, S-097 |
| R-009 | New chats start on Web. Checking or unchecking Manuscript or a source leaves Web as it was. Unchecking the last checked item, or choosing Clear selection, leaves only Web checked. Selection changes apply immediately to the next exchange in the same conversation. Writers can search the source list by title, and filtering preserves checked items. Keep Web, Manuscript and Clear selection visible while sources scroll. Arrow keys move focus, Space toggles and Escape returns focus to the Context button. Summarize the selection on the closed button. | from ticket | 25, 26 | S-064, S-065, S-066, S-071, S-074, S-076, S-080, S-086, S-087 |
| R-010 | Reopening a chat restores the Web and Manuscript settings and the source selection from its last successful exchange, so a failed send does not change them. A saved record with scope `none` shows as Web alone. A source that is no longer available is named by its saved title and the remaining choices stay checked. | from ticket | 27 | S-090, S-091 |

## Open Questions

- Embedding-model change before the reindex command runs: documents stay searchable with vectors from the old model until then, so a query could be scored against them. Suggestion, not yet built: record the embedding model on each indexed document and treat a document from another model as unavailable.
- The numeric relevance cutoff is not calibrated for production (T-008). `ASSISTANT_RELEVANCE_THRESHOLD` is unset by default, so with it unset a low-scoring passage can still be admitted and "searched without a match" cannot occur. The 0.6904 suggested by the calibration script was derived from question-style queries and needs rechecking with draft-bearing search text before it is set.
