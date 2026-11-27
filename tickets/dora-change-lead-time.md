# [dora-change-lead-time] As a Theseus maintainer, I can see how long merged feature pull requests take to reach production

## Intent

Give maintainers a baseline for how long merged features take to reach users.

## Context

Theseus runs on Render. Feature pull requests can reach production through a promotion from `staging` to `main` or through a direct merge into `main`.

## Scope

- Measure elapsed time from each feature pull request's original merge into `staging` or `main` to the first successful production deployment that includes its changes.
- Make the report available on demand in GitHub Actions. Publish a fresh report weekly after a maintainer verifies the on-demand results and enables weekly publication. Withhold scheduled publication while verification is pending.
- Show the UTC reporting window bounds, median lead time in hours, and count of included feature pull requests.

## Expected Outcomes

- [ ] A deployment that ships several qualifying feature pull requests produces one sample per pull request, including when one pull request contains several commits.
- [ ] A promotion preserves each feature pull request's original merge time, including when the promotion is squashed and the evidence identifies the original pull requests.
- [ ] A merged feature pull request stays out of the report until it successfully ships to production. A redeploy preserves its first live timestamp and counts the pull request only if that timestamp is within the window.
- [ ] A verified period with no qualifying feature pull requests shows a count of zero and marks the median as unavailable.
- [ ] When available evidence cannot establish the result, the manual or scheduled report fails with a sanitized diagnostic and withholds the median and count.

## Rules / Constraints

- Use the 30 days before the report starts. Include the UTC start boundary and exclude the UTC end boundary.
- Establish each feature pull request's first successful live deployment across verified history on the designated Render production service. Use that timestamp to determine window membership, even if the pull request merged before the window opened.
- Exclude preview and staging deployments and production attempts that never went live. Preserve historically successful live deployments after deactivation.
- Label the result “Feature PR merge-to-production lead time.”

## Non-Functional Requirements

- Keep credentials out of report output and logs.

## Out of Scope

- Per-commit lead time, PR-open-to-production lead time, and other DORA metrics.
- Changes to the existing Render deployment process.

## Open Questions

- Which Render service is production, and how far back can its deployment history be verified?
- Which merge strategies are enabled on `staging` and `main`, and what evidence identifies original feature pull requests when history is rewritten?
- Does the maintainer-approved feature classification cover historical pull requests?

## Output Paths

Feature directory `specs/devops/dora-change-lead-time/`.

- Intake brief: `brief.md`
- Gherkin: `gherkin.feature`
- Spec files: `requirements.md`, `design.md`, and `tasks.md`

## Definition of Done

- [ ] Intake generated and approved
- [ ] Gherkin generated and approved
- [ ] Open questions resolved
- [ ] Spec, Gherkin, and code in sync
- [ ] Reviewed and merged
