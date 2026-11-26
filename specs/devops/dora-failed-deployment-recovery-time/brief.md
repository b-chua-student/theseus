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
- Summarize completed recovery durations with the median and sample count.
- Show statuses and separate counts for unresolved failures and restored failures with missing timestamps.
- Let maintainers record qualifying production failures before a corrective deployment exists and report those failures and recoveries that occur without a corrective deployment.

## Non-Goals

- Changes to deployment operations.
- Changes to reporting for other metrics.

## Constraints

- Only production failures attributable to a deployment that require immediate intervention qualify.
- Failed deployment attempts that leave production service healthy are excluded.
- An unresolved failure has no completed recovery duration.
- The report counts each qualifying production incident once, including incidents addressed by multiple corrective deployments.

## Known Touchpoints

- The Theseus DevOps Time to Restore metric report.
- Production monitoring or a maintainer-confirmed incident timeline establishes when service degraded and when normal service was restored.
- Render deployment history links releases and corrective deployments to incidents. A corrective deployment's Live time can establish the restoration time when evidence confirms service recovered then.

## Assumptions

- The issue's exclusion of changes to deployment operations and other metric reporting is treated as scope guidance.

## Open Questions

- None.

## Success Criteria

1. The report shows the elapsed time from the verified start of production degradation to the verified restoration of normal service for a qualifying failure. It uses the corrective deployment's Render Live time as the restoration time when recovery at that time is confirmed.
2. The report excludes failures outside production, failures unattributable to deployments, failures that do not require immediate intervention, and failed deployment attempts that leave production service healthy.
3. The report shows unresolved failures as “Unresolved” and restored failures with either time unknown as “Missing timestamp.” It leaves their durations blank and shows separate counts for the two groups.
4. The report shows the median and count of qualifying completed recoveries with both timestamps. When the count is zero, it shows “No completed recoveries with known timestamps.”
5. A recorded qualifying failure appears in the report before any corrective deployment. A recovery confirmed without a corrective deployment is reported using the same timestamp and status rules.
6. A qualifying incident with multiple corrective deployments has one report entry. If both timestamps are known, its completed recovery contributes one duration to the median and one to the completed recovery count.

## Reference Links

- [GitHub issue #159](https://github.com/b-chua-student/theseus/issues/159)
- [DORA metric definitions](https://dora.dev/guides/dora-metrics/)
