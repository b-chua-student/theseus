# [dora-failed-deployment-recovery-time] As a maintainer, I can track failed deployment recovery time

This metric helps maintainers see how long it takes to restore production after a deployment failure.

## Intent
The Theseus DevOps requirements call this metric Time to Restore. [DORA metric definitions](https://dora.dev/guides/dora-metrics/)

## Context
- Measure elapsed time from a deployment-caused production failure that requires immediate intervention to restoration of normal service.

## Scope
- [ ] The report shows recovery durations for qualifying failures with known failure and restoration times.

## Expected Outcomes
- Limit the metric to production failures attributable to deployments. An unresolved failure has no completed recovery duration.

## Rules / Constraints
No additional non-functional requirements specified.

## Non-Functional Requirements
- Changes to deployment operations and reporting for other metrics.

## Out of Scope
- Which events establish failure and restoration? How should the report summarize durations and show unresolved failures?

## Open Questions
undefined

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
