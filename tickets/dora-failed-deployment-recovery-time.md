# [dora-failed-deployment-recovery-time] As a maintainer, I can track failed deployment recovery time

This metric helps maintainers see how long it takes to restore production after a deployment failure.

## Intent
The Theseus DevOps requirements call this metric Time to Restore. [DORA metric definitions](https://dora.dev/guides/dora-metrics/)

## Context
- Measure elapsed time from a deployment-caused production failure that requires immediate intervention to restoration of normal service.

## Scope
- [ ] The report shows recovery durations for qualifying failures with known failure and restoration times.
- [ ] Use production monitoring or a maintainer-confirmed incident timeline to establish when degradation began and when normal service was restored. Use the corrective deployment's Render Live time as the restoration time when evidence confirms service recovered then.
- [ ] Maintainers can record a qualifying production failure and see it in the recovery report before any corrective deployment. Record whether normal service has been restored separately from its restoration time. Include recoveries confirmed by monitoring or a maintainer-confirmed timeline when service is restored without a corrective deployment.
- [ ] Exclude failed deployment attempts that leave production service healthy.
- [ ] Show report entries only for qualifying failures. Exclude all other failures and deployment attempts from the median and from every report count.
- [ ] Show the median of completed recovery durations and the number included. When none can be calculated, show “No completed recoveries with known timestamps.”
- [ ] Count each qualifying production incident once, including when multiple corrective deployments respond to the same incident. A completed recovery with both timestamps contributes one duration to the median and one to the completed recovery count.
- [ ] Show unresolved failures as “Unresolved” and restored failures missing one or both timestamps as “Missing timestamp.” Leave their durations blank, exclude both groups from the median, and show their counts separately.
- [ ] When there are zero qualifying failures, show no incident entries, show zero for the completed recovery, unresolved, and missing-timestamp counts, and display “No completed recoveries with known timestamps.”
- [ ] Let maintainers refresh a dedicated recovery report on demand. Show the report run time in UTC and include all recorded qualifying incidents.
- [ ] Use the latest valid maintainer confirmation that explicitly resolves conflicting evidence. Until resolved, treat a disputed timestamp as unknown. For a restoration time earlier than degradation, treat the restoration timestamp as unknown until corrected. For restored incidents, apply the missing-timestamp rules and identify the incident and evidence problem.
- [ ] If incident records cannot be loaded, show that evidence is incomplete in place of the empty-report result.
- [ ] Keep the original record as the single recovery record for each incident. Let maintainers confirm the incident independently of any corrective deployment and associate subsequent corrective deployments with the original record, even if those deployments were recorded separately before being linked. Keep the incident confirmation and timeline on the original record and preserve the separately recorded deployment evidence.

## Expected Outcomes
- Limit the metric to production failures attributable to deployments. An unresolved failure has no completed recovery duration.

## Rules / Constraints
- None beyond the scope above.

## Non-Functional Requirements
- None specified.

## Out of Scope
- Changes to deployment operations or reporting for other metrics.

## Open Questions
- None.

## Output Paths
This feature lives in `specs/devops/dora-failed-deployment-recovery-time/`.

- Intake brief: `brief.md`
- Gherkin: `gherkin.feature`
- Spec files: `requirements.md`, `design.md`, and `tasks.md`

## Definition of Done
- [ ] Intake generated and approved
- [ ] Gherkin generated and approved
- [ ] Open questions resolved
- [ ] Spec, Gherkin, and code in sync
- [ ] Reviewed and merged
