# Requirements — Feature PR merge-to-production lead time

Use the [brief](brief.md) for scope and [lead-time.feature](lead-time.feature) for acceptance scenarios.

| ID | Acceptance criteria | Scenarios |
| --- | --- | --- |
| R1 | A maintainer can run the report on demand in GitHub Actions. A successful report is labeled “Feature PR merge-to-production lead time” and includes the UTC bounds of the rolling 30-day window, the included feature PR count, and the median lead time in hours. When the count is zero, the median is unavailable. | S-001, S-006 |
| R2 | Count each qualifying feature PR once, using its original merge timestamp and the time it first went live in production. Include PRs merged into staging and carried by a promotion, and PRs merged directly into main. Preserve each feature PR's identity and timestamp across multi-commit PRs, multi-PR promotions, and squash promotions with sufficient provenance. | S-001, S-009, S-011 |
| R3 | Qualify only successful live deployments on the designated Render production service. Use the first qualifying deployment across the available, verified history. Include a PR if that first live timestamp falls within the reporting window, even if it merged earlier. Exclude undeployed PRs and PRs first shipped before the window, including ones redeployed during it. | S-004–S-007 |
| R4 | Fail with a sanitized diagnostic and withhold the median and count when available evidence cannot establish the result. Keep credentials out of report output and workflow logs. | S-008, S-010 |
| R5 | Publish a fresh report weekly after a maintainer verifies the on-demand results and enables publication. Keep scheduled publication withheld while verification is pending. Apply R4 to scheduled runs as well. | S-002, S-003 |

The scope covers one sample per feature PR. Per-commit measurements, other DORA metrics, and changes to the Render deployment process are outside this scope.
