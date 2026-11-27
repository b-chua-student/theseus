# [dora-deployment-rework-rate] As a maintainer, I can track deployment rework rate

## Intent
This metric helps maintainers see what share of production deployments are unplanned responses to incidents.

## Context
This metric is part of DORA’s current software delivery metrics. [DORA metric definitions](https://dora.dev/guides/dora-metrics/)

## Scope
- Report the percentage of production deployments that are unplanned and made in response to a production incident.

## Expected Outcomes
- [ ] A maintainer can run the report on demand for the preceding 30 days in UTC.
- [ ] With complete evidence and a positive production deployment total, the report shows the confirmed rework count, the production deployment total, and the resulting percentage. If none qualify, show 0%.
- [ ] When production history verifies an empty period, show zero for both counts and display **N/A — no production deployments** for the rate.
- [ ] When missing evidence could change either count, show **Incomplete evidence** and withhold the percentage. If production history is complete, show the verified total, confirmed rework count, and count of deployments whose rework status could change because of unavailable evidence. Otherwise mark the production total as unverified.
- [ ] The production incident template includes a **Deployment rework** section explaining how a maintainer records that a specific deployment went live in production as an unplanned response to the incident.

## Rules / Constraints
- Count each qualifying deployment once. Include all production deployments in the denominator for the reporting period.
- Count a deployment as rework when production history confirms it went live and a maintainer confirms on the incident record that the specific deployment was an unplanned response to a production incident. The incident can have any cause.
- Assign deployments to the period by their production live time. Include the window start and exclude the report start, regardless of when the incident began.
- With readable incident evidence, a deployment with no valid rework confirmation contributes only to the production total. No separate review or no-rework confirmation is required.
- When incident evidence is unavailable and could establish rework for a deployment, count that deployment once as affected by the evidence gap. If the affected IDs are unknown, include every deployment that could still be confirmed as rework. Keep valid rework confirmations that the gap cannot change.

## Non-Functional Requirements
No additional non-functional requirements specified.

## Out of Scope
- Changes to deployment operations and reporting for other metrics.

## Open Questions
- None.

## Output Paths
This feature lives in `specs/devops/dora-deployment-rework-rate/`.

- Intake brief: `brief.md`
- Gherkin: `gherkin.feature`
- Spec files: `requirements.md`, `design.md`, and `tasks.md`
- Scenario IDs: `@S-064` through `@S-074`, assigned to avoid collisions in the DevOps context.

## Definition of Done
- [X] Intake generated and approved
- [X] Gherkin generated and approved
- [X] Open questions resolved
- [ ] Spec, Gherkin, and code in sync
- [ ] Reviewed and merged
