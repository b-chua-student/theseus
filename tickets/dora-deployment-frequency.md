# [dora-deployment-frequency] As a maintainer, I can track deployment frequency

## Intent
This metric helps maintainers see how often Theseus delivers changes to production.

## Context
The Theseus DevOps requirements call for this metric. [DORA metric definitions](https://dora.dev/guides/dora-metrics/)

## Scope
- Report the elapsed time between consecutive production deployments.

## Expected Outcomes
- [ ] Each interval runs from when one deployment reached production to when the next deployment reached production.
- [ ] The report indicates that an interval is unavailable when fewer than two deployments have reached production.

## Rules / Constraints
- Exclude staging and deployment attempts that never reach production.
- Apply the same measurement rules to manually triggered deployments.
- Run the report on each merge into main.
- Use the complete production deployment history available at report time, with no time cutoff.
- Count every successful production deployment, including successful rollbacks and redeployments. Exclude unsuccessful rollbacks and redeployments.

## Non-Functional Requirements
No additional non-functional requirements specified.

## Out of Scope
- Changes to deployment operations and reporting for other metrics.

## Open Questions
- None.

## Output Paths
This feature lives in `specs/devops/dora-deployment-frequency/`.

- Intake brief: `brief.md`
- Gherkin: `gherkin.feature`
- Spec files: `requirements.md`, `design.md`, and `tasks.md`

## Definition of Done
- [ ] Intake generated and approved
- [ ] Gherkin generated and approved
- [x] Open questions resolved
- [ ] Spec, Gherkin, and code in sync
- [ ] Reviewed and merged
