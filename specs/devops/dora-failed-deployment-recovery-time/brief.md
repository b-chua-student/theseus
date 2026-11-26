# Brief: Track failed deployment recovery time

- ID: dora-failed-deployment-recovery-time
- Owner: Unspecified in issue #159
- Date: 2026-11-26
- Base SHA: bf695fe6a14c393e5a8a1c20dc0c637d6faeb664

## Goal

Help maintainers see how long it takes to restore normal production service after a deployment failure. The Theseus DevOps requirements call this metric Time to Restore.

## Users / Roles

- Maintainers who track production recovery after deployment failures.

## In Scope

- Report individual recovery durations for qualifying failures with known failure and restoration times.
- Measure elapsed time from the production failure to restoration of normal service.

## Non-Goals

- Changes to deployment operations.
- Changes to reporting for other metrics.

## Constraints

- Only production failures attributable to a deployment that require immediate intervention qualify.
- An unresolved failure has no completed recovery duration.

## Known Touchpoints

- The Theseus DevOps Time to Restore metric report.

## Assumptions

- The issue's exclusion of changes to deployment operations and other metric reporting is treated as scope guidance.

## Open Questions

- Deferred: Which events establish failure and restoration? The ticket leaves the event sources open.
- Deferred: How should the report summarize durations and show unresolved failures? The ticket defines individual recovery durations and leaves summary and presentation rules open.

## Success Criteria

1. The report shows the elapsed time from failure to restoration of normal service for a qualifying production failure with both times known.
2. The report excludes failures outside production, failures unattributable to deployments, and failures that do not require immediate intervention from the metric.
3. The report shows no completed recovery duration for an unresolved failure or a qualifying failure with either time unknown.

## Reference Links

- [GitHub issue #159](https://github.com/b-chua-student/theseus/issues/159)
- [DORA metric definitions](https://dora.dev/guides/dora-metrics/)
