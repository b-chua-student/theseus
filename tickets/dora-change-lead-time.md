# [dora-change-lead-time] As a Theseus maintainer, I can see how long merged feature pull requests take to reach production

## Intent

Give maintainers a baseline for how long merged features take to reach users.

## Context

Theseus runs on Render. Feature pull requests can reach production through a promotion from `staging` to `main` or through a direct merge into `main`.

Production deployments from `main` on the designated Render service are initiated manually by a maintainer. The full deployment history is available for verification.

Pull requests into `staging` and `main` allow merge commits only.

All staging-to-main promotions in the production history used by the report used merge commits.

Git history confirms that the AI Research Assistant PR (#96) and the staging-to-main promotions in PRs #109, #112, #153, #167, and #173 used merge commits.

## Scope

- Measure elapsed time from each feature pull request's original merge into `staging` or `main` to the first successful production deployment that includes its changes.
- Run the report only when a maintainer starts it manually in GitHub Actions.
- Show the UTC reporting window bounds, median lead time in hours, and count of included feature pull requests.

## Expected Outcomes

- [ ] A deployment that ships several qualifying feature pull requests produces one sample per pull request, including when one pull request contains several commits.
- [ ] A promotion preserves each feature pull request's original merge time, including when the promotion is squashed and the evidence identifies the original pull requests.
- [ ] A merged feature pull request stays out of the report until it successfully ships to production. A redeploy preserves its first live timestamp and counts the pull request only if that timestamp is within the window.
- [ ] A verified period with no qualifying feature pull requests shows a count of zero and marks the median as unavailable.
- [ ] When available evidence cannot establish the result, the report fails with a sanitized diagnostic and withholds the median and count.

## Rules / Constraints

- Maintainers configure the feature pull request label as a GitHub Actions repository variable. For Theseus, set it to `enhancement`. Use the configured label for historical pull requests in scope as well.
- Use the 30 days before the report starts. Include the UTC start boundary and exclude the UTC end boundary.
- Establish each feature pull request's first successful live deployment across verified history on the designated Render production service. Use that timestamp to determine window membership, even if the pull request merged before the window opened.
- Use deployment history from before the reporting window when needed to distinguish a first live deployment from a redeploy.
- Require maintainer-reviewed evidence identifying the original feature pull requests carried by a promotion when rewritten history obscures that link.
- Exclude preview and staging deployments and production attempts that never went live. Preserve historically successful live deployments after deactivation.
- Label the result “Feature PR merge-to-production lead time.”
- Report runs read deployment history and never initiate a production deployment.

## Non-Functional Requirements

- Keep credentials out of report output and logs.

## Out of Scope

- Per-commit lead time, PR-open-to-production lead time, and other DORA metrics.
- Changes to the existing Render deployment process.

## Open Questions

- None.

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
