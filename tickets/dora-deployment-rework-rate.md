# [dora-deployment-rework-rate] As a maintainer, I can track deployment rework rate

## Intent
This metric helps maintainers see what share of production deployments are unplanned responses to incidents.

## Context
This metric is part of DORA’s current software delivery metrics. [DORA metric definitions](https://dora.dev/guides/dora-metrics/)

## Scope
- Report the percentage of production deployments that are unplanned and made in response to a production incident.

## Expected Outcomes
- [ ] The report shows the number of qualifying rework deployments, the total number of production deployments, and the resulting percentage when the total is greater than zero.

## Rules / Constraints
- Count each qualifying deployment once. Include all production deployments in the denominator for the reporting period.

## Non-Functional Requirements
No additional non-functional requirements specified.

## Out of Scope
- Changes to deployment operations and reporting for other metrics.

## Open Questions
- What evidence establishes that a deployment was unplanned and incident-driven? How should periods with no deployments or incomplete evidence appear?

## Output Paths
This feature lives in `specs/devops/dora-deployment-rework-rate/`.

- Intake brief: `brief.md`
- Gherkin: `gherkin.feature`
- Spec files: `requirements.md`, `design.md`, and `tasks.md`

## Definition of Done
- [X] Intake generated and approved
- [X] Gherkin generated and approved
- [X] Open questions resolved
- [ ] Spec, Gherkin, and code in sync
- [ ] Reviewed and merged
