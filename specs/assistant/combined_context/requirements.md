# Requirements — Compare a manuscript with selected library sources

- Ticket: `tickets/120.md`

## Requirements

| ID | Requirement | Source | Ticket lines | Scenarios |
| --- | --- | --- | --- | --- |
| R-001 | A writer can ask one question using the current manuscript, including unsaved edits, together with selected library sources. | from ticket | 5, 13 | S-063, S-064, S-067, S-068 |
| R-002 | When asked which selected sources support a manuscript claim, the Assistant identifies the supporting sources using manuscript and source evidence in the same answer. | from ticket | 18 | S-068 |
| R-003 | A writer can quote a selected manuscript passage and receive a comparison addressing that specific passage using evidence from the selected sources. | from ticket | 14, 19 | S-069, S-075 |
| R-004 | Only library sources selected by the writer may supply library evidence for the answer. | from ticket | 23 | S-064, S-068, S-070, S-072, S-073, S-077 |

## Open Questions

- Lines 35–36 leave bulk selection and unavailable or unmatched evidence open. The brief proposes a fixed snapshot of all indexed sources and distinct per-source outcomes for unavailable, unmatched and capacity-omitted evidence. Confirm these in the ticket before implementing their scenarios.
- The brief also proposes Web selection and fallback, keyboard and filter behavior, conversation continuity and restoration, quote-only sharing, large selections, relevance calibration and fair passage allocation. Confirm these additions in the ticket before treating them as acceptance requirements. Scenario references above identify coverage of the ticketed behavior, not approval of every assertion in a scenario.
