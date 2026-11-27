# [pr-merge-to-production-lead-time] As a Theseus maintainer, I can see how long merged pull requests take to reach production

## Intent

Give maintainers a baseline for how long merged changes take to reach users.

## Context

Theseus runs on Render. The DevOps brief defines lead time for changes as time from merge to deployment.

## Scope

- Measure elapsed time from each pull request's merge into the production branch to the first successful production deployment that includes its changes.
- Make the report available on demand in GitHub Actions and publish it weekly once the results are verified.
- Show the reporting period, median lead time, and number of included pull requests for a rolling 30-day window.

## Expected Outcomes

- [ ] A deployment that ships several pull requests produces a separate lead-time sample for each.
- [ ] A merged pull request stays out of the median until it successfully ships to production.
- [ ] A redeploy does not change a pull request's first deployment time or add a second sample.
- [ ] A period with no qualifying pull requests shows a count of zero and marks the median as unavailable.

## Rules / Constraints

- Include a pull request when its first successful production deployment falls within the reporting window, even if it merged before the window opened.
- Exclude previews, staging, and unsuccessful deployments.
- Label the result as PR merge-to-production lead time.

## Non-Functional Requirements

- Keep credentials out of report output and logs.

## Out of Scope

- Other DORA metrics and PR-open-to-production lead time.
- Changes to the existing Render deployment process.

## Open Questions

- Which Render service and branch should be treated as production?

## Output Paths

Feature directory `specs/devops/pr-merge-to-production-lead-time/`.

- Intake brief `brief.md`
- Gherkin `gherkin.feature`
- Spec files `requirements.md`, `design.md`, and `tasks.md`

## Definition of Done

- [ ] Intake generated and approved
- [ ] Gherkin generated and approved
- [ ] Open questions resolved
- [ ] Spec, Gherkin, and code in sync
- [ ] Reviewed and merged
