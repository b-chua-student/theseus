# Requirements — Track DORA deployment frequency

- Ticket: `tickets/dora-deployment-frequency.md`

## Requirements

| ID | Requirement | Source | Ticket lines | Scenarios |
| --- | --- | --- | --- | --- |
| R-001 | Report one elapsed interval for each consecutive pair of production deployments, measured between the times they reached production. | from ticket | 10, 13 | S-023 |
| R-002 | Exclude staging deployments and attempts that never reach production from the interval calculation. | from ticket | 17 | S-024 |
| R-003 | Apply the same eligibility and interval calculation rules to manually triggered deployments. | from ticket | 18 | S-021 |
| R-004 | Indicate that an interval is unavailable when fewer than two deployments have reached production. | from ticket | 14 | S-022 |

## Open Questions

- How often should the report run?
- What deployment history window should the report use?
- Which rollbacks and redeployments qualify as production deployments?
