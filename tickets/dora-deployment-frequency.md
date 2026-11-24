# [dora-deployment-frequency] As a maintainer, I can track deployment frequency

## Intent
This metric helps maintainers see how often Theseus delivers changes to production.

## Context
The Theseus DevOps requirements call for this metric. [DORA metric definitions](https://dora.dev/guides/dora-metrics/)

## Scope
- Report the count of deployments that reach production in a reporting period.

## Expected Outcomes
- [ ] The report identifies the period and counts each deployment that reached production once.

## Rules / Constraints
- Exclude staging and deployment attempts that never reach production.

## Non-Functional Requirements
No additional non-functional requirements specified.

## Out of Scope
- Changes to deployment operations and reporting for other metrics.

## Open Questions
- What reporting period and cadence should we use? How should rollbacks and redeployments be counted?

## Output Paths
This feature lives in `specs/devops/dora-deployment-frequency/`.

- Intake brief: `brief.md`
- Gherkin: `gherkin.feature`
- Spec files: `requirements.md`, `design.md`, and `tasks.md`

## Definition of Done
- [ ] Intake generated and approved
- [ ] Gherkin generated and approved
- [ ] Open questions resolved
- [ ] Spec, Gherkin, and code in sync
- [ ] Reviewed and merged
