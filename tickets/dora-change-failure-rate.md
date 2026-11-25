# [dora-change-failure-rate] As a maintainer, I can track change failure rate

## Intent
This metric helps maintainers see how often production changes require immediate intervention.

## Context
The Theseus DevOps requirements call for this metric. [DORA metric definitions](https://dora.dev/guides/dora-metrics/)

Theseus deploys to production on Render, where maintainers can review production deployment history.

## Scope
- Report the percentage of production deployments that require immediate intervention, such as a rollback or hotfix.
- Let maintainers run the report on demand and run it automatically after each merge into main.

## Expected Outcomes
- [ ] The report shows the number of production deployments requiring intervention, the total number of production deployments, and the resulting percentage when the total is greater than zero.
- [ ] A maintainer can start a report on demand.
- [ ] Each merge into main starts a report automatically.

## Rules / Constraints
- Count each qualifying deployment once, even if it requires several interventions.

## Non-Functional Requirements
No additional non-functional requirements specified.

## Out of Scope
- Changes to deployment operations and reporting for other metrics.

## Open Questions
- What evidence links an intervention to a deployment? What qualifies as immediate, and how should periods with no deployments or incomplete evidence appear?

## Output Paths
This feature lives in `specs/devops/dora-change-failure-rate/`.

- Intake brief: `brief.md`
- Gherkin: `gherkin.feature`
- Spec files: `requirements.md`, `design.md`, and `tasks.md`

## Definition of Done
- [ ] Intake generated and approved
- [ ] Gherkin generated and approved
- [ ] Open questions resolved
- [ ] Spec, Gherkin, and code in sync
- [ ] Reviewed and merged
