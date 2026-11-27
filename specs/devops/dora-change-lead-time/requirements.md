# Requirements — Feature PR merge-to-production lead time

- Ticket: `tickets/dora-change-lead-time.md`

## Requirements

| ID | Requirement | Source | Ticket lines | Scenarios |
| --- | --- | --- | --- | --- |
| R-001 | Run the report on demand in GitHub Actions. Show the named metric, UTC window bounds, included PR count, and median in hours. Show an unavailable median for a verified zero count. | from ticket | 22, 23, 30, 41 | S-001, S-006 |
| R-002 | Count one sample per qualifying PR from its original merge into staging or main. Identify features by the enhancement label and require maintainer-reviewed evidence when rewritten promotion history obscures PR identity. | from ticket | 9, 21, 27, 28, 35, 39 | S-001, S-009, S-010, S-011, S-076 |
| R-003 | Use the earliest successful live timestamp on the designated production service, including prior verified history and deactivated deployments. Include only first live timestamps in the 30 days before report start, including the UTC start and excluding the UTC end. | from ticket | 29, 36, 37, 38, 40 | S-004, S-005, S-006, S-007, S-075, S-077 |
| R-004 | Fail with a sanitized diagnostic and withhold the median and count when evidence is insufficient. Keep credentials out of reports and logs. | from ticket | 31, 46 | S-008, S-010 |
| R-005 | Start the report only when manually requested by a maintainer. | from ticket | 22 | S-001, S-078 |
| R-006 | Maintainers initiate production deployments manually from main. Report runs read deployment history without initiating deployments. | from ticket | 11, 42, 51 | S-001, S-011 |

## Open Questions

- None.
