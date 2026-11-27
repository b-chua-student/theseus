# Brief: Scheduled DORA metrics report

- ID: dora-scheduled-report
- Owner: Theseus maintainers
- Date: 2026-11-27
- Base SHA: f7e1655f2b83ab25563b6313b5855a00d813f0d0

## Goal

Publish one Markdown report per run, both weekly and on demand, so maintainers can review all five DORA metrics together.

## Users / Roles

- Theseus maintainers who review production delivery and recovery.

## In Scope

- Start the report automatically every Sunday at 00:00 Manila time (Saturday at 16:00 UTC).
- Let Theseus maintainers start the same report manually.
- Generate a report for deployment frequency, feature PR merge-to-production lead time, change failure rate, failed deployment recovery time, and deployment rework rate.
- Display the report on the run page and make the same Markdown available for download.
- Identify unavailable metrics and publish results available for the other metrics.

## Non-Goals

- Starting deployments, changing incident records, redefining metrics, or committing generated reports to the repository.

## Constraints

- Use each metric's existing definition, evidence rules, and reporting period.
- Preserve the existing individual report entry points.
- Publish the generation time in UTC and omit credentials.
- Place the downloadable Markdown file under `reports/dora/` in each run’s output.

## Known Touchpoints

- Existing individual DORA reports and the consolidated report display for scheduled and manual runs.

## Assumptions

- Each scheduled or manual run publishes one consolidated report.

## Open Questions

- None.

## Success Criteria

1. The scheduled run starts every Sunday at 00:00 Manila time (Saturday at 16:00 UTC) without maintainer action and publishes a consolidated report.
2. The displayed report and downloadable Markdown have matching content with all five metric sections and the UTC generation timestamp. The downloadable output contains one Markdown report under `reports/dora/`. The report contains no credentials.
3. A metric with unavailable evidence identifies its gap while the other available results remain visible.
4. Both scheduled and manual runs use the existing metric rules, preserve individual reports, and leave deployments, incident records, and repository files unchanged.
5. A Theseus maintainer can manually start a run outside the scheduled time and get the same report format and publication options.

## Reference Links

- [Source ticket](../../../tickets/dora-scheduled-report.md)
