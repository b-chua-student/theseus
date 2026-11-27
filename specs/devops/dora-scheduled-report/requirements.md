# Requirements — Scheduled DORA metrics report

- Ticket: `tickets/dora-scheduled-report.md`

## Requirements

| ID | Requirement | Source | Ticket lines | Scenarios |
| --- | --- | --- | --- | --- |
| R-001 | Schedule the consolidated report every Sunday at 00:00 Manila time (Saturday at 16:00 UTC) and publish automatically when the scheduled run starts. | from ticket | 13, 20 | S-079 |
| R-002 | Let Theseus maintainers run the consolidated report on demand outside the scheduled time with the same format and publication options. | from ticket | 14, 21 | S-081 |
| R-003 | Publish one downloadable Markdown file per run under `reports/dora/`. | from ticket | 15 | S-079, S-081 |
| R-004 | Display the full contents of the downloadable Markdown on the run page, splitting the display into ordered sections when needed to fit the size limit. | from ticket | 15, 22 | S-079, S-081, S-083 |
| R-005 | Include sections for deployment frequency, feature PR merge-to-production lead time, change failure rate, failed deployment recovery time, and deployment rework rate. | from ticket | 9, 16, 22 | S-079, S-081 |
| R-006 | Show the report generation time in UTC. | from ticket | 16, 22 | S-079, S-081 |
| R-007 | Explain unavailable evidence in the affected metric's section and publish the results available for the other metrics. | from ticket | 23 | S-080 |
| R-008 | Use each metric's existing definition, evidence rules, and reporting period. | from ticket | 27, 37 | S-079, S-081 |
| R-009 | Preserve all individual report entry points, including the standalone on-demand lead time report. | from ticket | 28 | S-079, S-081 |
| R-010 | Keep credentials out of the published report. | from ticket | 32 | S-079, S-081 |
| R-011 | Generate the report without starting a production deployment, changing incident records, or committing reports to the repository. | from ticket | 36, 37 | S-079 |
| R-012 | Recover a dropped scheduled run only through a manual run started by a maintainer. | from ticket | 14 | S-082 |

## Open Questions

- None.
