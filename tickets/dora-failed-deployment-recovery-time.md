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
- [ ] Show the median of completed recovery durations and the number included. When none can be calculated, show “No completed recoveries with known timestamps.”
- [ ] Show unresolved failures as “Unresolved” and restored failures missing either time as “Missing timestamp.” Leave their durations blank, exclude both groups from the median, and show their counts separately.

## Expected Outcomes
- Limit the metric to production failures attributable to deployments. An unresolved failure has no completed recovery duration.

## Rules / Constraints
No additional non-functional requirements specified.

## Non-Functional Requirements
- Changes to deployment operations and reporting for other metrics.

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
