# Brief: Track DORA deployment frequency

- ID: #157
- Owner: @b-chua-student
- Date: 2026-11-24
- Base SHA: `2bb7768f0ba278d5b4887e2d4c8f893e4c6d2218`

## Goal

Report elapsed time between production deployments so Theseus maintainers can see how often changes reach production.

## Users / Roles

- Theseus maintainers review deployment frequency.

## In Scope

- Report the elapsed time between consecutive production deployments.

## Non-Goals

- Changes to deployment operations.
- Reporting for other metrics.

## Constraints

- Measure each interval using the times when the two deployments reached production.
- Exclude staging deployments and deployment attempts that never reach production.
- Apply the same measurement rules to manually triggered deployments.
- Use the complete production deployment history available at report time.
- Count every successful production deployment, including rollbacks and redeployments.

## Known Touchpoints

- The Theseus DevOps requirements call for tracking deployment frequency.

## Assumptions

- No assumptions were recorded in the ticket.

## Open Questions

- None.

## Success Criteria

1. The report shows the elapsed time between each pair of consecutive production deployments.
2. Staging deployments and attempts that never reach production do not create or split an interval.
3. A manually triggered deployment that reaches production can form an interval with another production deployment. A manual attempt that never reaches production does not affect that interval.
4. When fewer than two deployments have reached production, the report indicates that an interval is unavailable.

5. Each merge into main triggers a deployment frequency report.
6. The report includes intervals from the earliest successful production deployment onward, regardless of age.
7. Successful rollbacks and redeployments contribute intervals. Unsuccessful attempts do not.

## Reference Links

- [GitHub issue #157](https://github.com/b-chua-student/theseus/issues/157)
- [DORA metric definitions](https://dora.dev/guides/dora-metrics/)
