# [dora-scheduled-report] As a Theseus maintainer, I can review DORA metrics on a schedule or on demand

## Intent

Give maintainers a recurring view of production delivery and recovery metrics in a single Markdown report.

## Context

Theseus reports deployment frequency, feature PR merge-to-production lead time, change failure rate, failed deployment recovery time, and deployment rework rate separately.

## Scope

- Generate a consolidated report automatically every Sunday at 00:00 Manila time (Saturday at 16:00 UTC).
- Allow Theseus maintainers to run the same consolidated report on demand.
- Publish one downloadable Markdown file per run under `reports/dora/` and display its contents on the run page.
- Include all five existing metrics and the report generation time in UTC.

## Expected Outcomes

- [ ] A run starts every Sunday at 00:00 Manila time without maintainer action and publishes the Markdown report.
- [ ] A maintainer can manually start a run outside the scheduled time and get the same report format and publication options.
- [ ] The displayed report and the downloaded file contain the same five metric sections and the UTC generation time.
- [ ] If evidence for one metric is unavailable, its section explains the gap and the report still shows results available for the other metrics.

## Rules / Constraints

- Use each existing metric's definition, evidence rules, and reporting period.
- Keep the existing entry points for individual reports. The consolidated report adds scheduled and manually triggered calculation of lead time alongside its existing on-demand report.

## Non-Functional Requirements

- Keep credentials out of the published report.

## Out of Scope

- Starting a production deployment or changing incident records.
- Changing metric definitions or committing generated reports to the repository.

## Open Questions

- None.

## Output Paths
Each feature lives in `specs/<context>/<feature_name>/`.

- Intake brief: `brief.md`
- Gherkin: `gherkin.feature`
- Spec files: `requirements.md`, `design.md`, and `tasks.md`

## Definition of Done
- [ ] Intake generated and approved
- [ ] Gherkin generated and approved
- [ ] Open questions resolved
- [ ] Spec, Gherkin, and code in sync
- [ ] Reviewed and merged
