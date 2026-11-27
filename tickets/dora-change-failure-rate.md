# [dora-change-failure-rate] As a maintainer, I can track change failure rate

## Intent
This metric helps maintainers see how often production changes require immediate intervention.

## Context
The Theseus DevOps requirements call for this metric. [DORA metric definitions](https://dora.dev/guides/dora-metrics/)

Theseus deploys to production on Render, where maintainers can review production deployment history.

## Scope
- Report the percentage of production deployments that require immediate intervention, such as a rollback or hotfix.
- Let maintainers run the report on demand and run it automatically after each merge into main.
- Automatically create a GitHub incident issue when a production rollback or a hotfix from a pull request labeled `production-hotfix` goes live. Update an explicitly linked GitHub incident issue when one exists.

## Expected Outcomes
- [ ] With complete evidence and at least one production deployment, the report shows the number requiring immediate intervention, the total, and the resulting percentage.
- [ ] When production history confirms there were no deployments, the report shows zero for both counts and marks the rate unavailable.
- [ ] When evidence is incomplete, the report marks the rate unavailable, identifies the missing evidence, and labels any displayed counts as confirmed so far.
- [ ] Manual and automatic reports display both bounds of a rolling 30-day period ending 24 hours before the run starts. Include deployments that went live after the start and at or before the cutoff.
- [ ] A maintainer can start a report on demand.
- [ ] Each merge into main starts a report automatically.
- [ ] Each qualifying corrective deployment is recorded on one GitHub incident issue, with a link to the corrective action and attribution pending maintainer confirmation.
- [ ] Reprocessing a corrective deployment does not create another issue or duplicate its entry on an existing issue.

## Rules / Constraints
- Use Render production deployment history for the total.
- Count an intervention only when a maintainer-confirmed incident record states that the original deployment caused the issue and records its Render deploy ID, the intervention type and start time, and a link to the rollback deployment or hotfix pull request.
- An intervention qualifies if it starts within 24 hours of the original deployment going live, including exactly 24 hours. Attribute it to the original deployment's reporting period.
- Pending attribution makes the rate unavailable if confirming the incident could add an original deployment to the intervention count under the 24-hour rule. Identify that pending incident as missing evidence. If pending attribution cannot change the count, publish the rate when there is at least one eligible deployment and the rest of the evidence is complete.
- Count each qualifying original deployment once, even if it requires several interventions.
- Both newly created incident issues and updates to linked incidents record the corrective deployment. A maintainer confirms which original deployment caused the incident.
- Apply `production-hotfix` to the original hotfix pull request, whether it targets `staging` or `main`. For a hotfix merged into `staging`, recognize it when it reaches production through an unlabeled promotion pull request into `main`.
- If an incident issue already exists, link it from the original hotfix pull request.

## Non-Functional Requirements
No additional non-functional requirements specified.

## Production Readiness

- [ ] If a maintainer-confirmed incident references a corrective deployment that cannot be verified as live in production, or its action does not match the recorded incident entry, exclude that attribution from the confirmed count. If it could change the count, identify the incident and missing evidence and mark the rate unavailable.
- [ ] If an earlier deployment has unresolved hotfix provenance, still record a later rollback or hotfix whose corrective action can be verified independently. Identify unresolved provenance in the report when it could affect the count.
- [ ] Include both workflows, their implementation, and their tests in the reviewed release. Verify production access, the deployment history and its starting point, rollback evidence before and after deactivation, and any required staging promotion mappings. Verify both report triggers and incident creation, linked updates, maintainer attribution, and replay with the permissions used in production.

## Out of Scope
- Changes to deployment operations and reporting for other metrics.

## Open Questions
- None.

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
