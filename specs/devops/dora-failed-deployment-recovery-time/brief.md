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
- Let maintainers refresh a dedicated report on demand for all recorded qualifying incidents and see the report run time in UTC.
- Identify disputed and out-of-order timeline evidence. Identify when incident records cannot be loaded.

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
   These failures and deployment attempts have no report entries and contribute to neither the median nor any report count.
3. The report shows unresolved failures as “Unresolved” and restored failures missing one or both timestamps as “Missing timestamp.” It leaves their durations blank and shows separate counts for the two groups.
4. The report shows the median and count of qualifying completed recoveries with both timestamps. When the count is zero, it shows “No completed recoveries with known timestamps.”
   When there are zero qualifying failures, the report also shows no incident entries and all three counts are zero.
5. A recorded qualifying failure appears in the report before any corrective deployment. A recovery confirmed without a corrective deployment is reported using the same timestamp and status rules.
6. A qualifying incident with multiple corrective deployments has one report entry. If both timestamps are known, its completed recovery contributes one duration to the median and one to the completed recovery count.
7. On demand, a maintainer can refresh the dedicated report and see all recorded qualifying incidents and the run time in UTC.
8. A restored incident with a disputed timestamp or a restoration time earlier than degradation is reported as “Missing timestamp” with a blank duration and an incident-specific diagnostic. The latest valid maintainer confirmation that explicitly resolves a conflict supplies the corrected timeline.
9. If incident records cannot be loaded, the report shows that evidence is incomplete.
10. Maintainers can confirm a qualifying incident before a correction exists and link later corrective deployments to the original record, even if the deployments were recorded separately. The original record retains the incident confirmation and timeline, shows the linked deployments, and is the only recovery record for that incident. The separately recorded deployment evidence remains available.

## Reference Links

- [GitHub issue #159](https://github.com/b-chua-student/theseus/issues/159)
- [DORA metric definitions](https://dora.dev/guides/dora-metrics/)
