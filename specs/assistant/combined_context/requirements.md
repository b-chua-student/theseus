# Requirements - Compare a manuscript with selected library sources

- Ticket: `tickets/120.md`

## Requirements

| ID | Requirement | Source | Ticket lines | Scenarios |
| --- | --- | --- | --- | --- |
| R-001 | A writer can select library sources together with the current manuscript and ask one question about both. | from ticket | 13, 18 | S-063, S-064, S-065, S-066, S-076, S-080, S-084, S-086, S-087 |
| R-002 | A combined question uses the current manuscript, including unsaved edits. | from ticket | 5, 13 | S-067, S-070 |
| R-003 | The answer identifies which selected sources support a manuscript claim, using the manuscript and evidence from the selected sources together. | from ticket | 18 | S-068, S-078 |
| R-004 | A writer can quote a selected passage and receive a comparison that addresses that passage using evidence from the selected sources. | from ticket | 14, 19 | S-069, S-075, S-088, S-089 |
| R-005 | Only the sources the writer selected may supply library evidence. | from ticket | 23 | S-068, S-070, S-072, S-073, S-077 |

## Open Questions

Ticket lines 35 and 36 are still open questions, and the intake adds refinements the ticket does not state. The items below document the proposed behavior and its scenario coverage. Scenario references in the table above identify coverage of the ticketed behavior, not approval of every assertion in a scenario.

- **Bulk selection (line 35).** The intake proposes one "All indexed sources" checkbox. It checks every source indexed at that moment, including entries hidden by the title filter, and preserves Web and Manuscript. Unchecking one source clears the indicator, and checking every source restores it. The option is disabled when no source is indexed. Sources indexed afterward stay unchecked until selected. Scenarios: S-081, S-082, S-083, S-093.
- **Evidence gaps (line 36).** The intake proposes the following:
  - Name each selected source that is unavailable and say it could not be checked.
  - Name each source that was searched without a match and say no relevant passage was found.
  - Continue with the usable evidence.
  - If none is usable, say the claim could not be verified from the selection.
  - Never call a claim contradicted on missing evidence alone.
  - With Web enabled, distinguish general knowledge from findings attributed to selected sources.

  Scenarios: S-079, S-085.
- **Relevance, coverage and capacity.** The intake proposes the following:
  - Search every selected source and rank passages by cosine similarity.
  - Admit only passages at or above the configured relevance threshold.
  - Set no fixed passage quota, so one source cannot crowd out another.
  - Fit evidence into the model's context window, name each source omitted for capacity, and cite only evidence supplied to the model.
  - Search selections larger than the current 1,000-ID request limit in full.

  Scenarios: S-092, S-094, S-095, S-096. The threshold and the passage budget have no values yet. They are set by calibration and testing (D-007, T-009).
- **Selection and conversation refinements.** The intake proposes the following:
  - Selection changes take effect immediately, with no Apply step.
  - Keyboard operation: arrow keys, Space and Escape.
  - Web, Manuscript and Clear selection stay visible while the source list scrolls.
  - Filtering keeps checked items checked.
  - The closed button summarizes the selection.

  Scenarios: S-071, S-074.
- **Saved conversations.** The intake proposes the following:
  - Reopening a chat restores the Web and Manuscript settings and the source selection from the last successful exchange.
  - A saved record with scope `none` shows as Web alone.
  - A source that is no longer available is named and the remaining choices stay checked.
  - The restore mapping for legacy `manuscript` and `source_library` records is not specified (D-006 proposes Manuscript alone or the saved sources, each with Web off).

  Scenarios: S-090, S-091.
