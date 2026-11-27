# Brief: Report feature PR merge-to-production lead time

- Origin: issue #140
- Scope: trace feature PRs from their original merge into staging or main to production.

## Goal

Give Theseus maintainers a baseline for how long a merged feature PR takes to go live in production.

## In Scope

- Trace feature PRs merged into `staging` through their promotion to `main`, and trace feature PRs merged directly into `main`.
- Measure one sample per feature PR from its merge timestamp to its first successful production deployment. A promotion can carry multiple feature PRs, each with its own merge timestamp.
- Report the UTC bounds of a rolling 30-day window, median lead time in hours, and included PR count only when a maintainer starts the report manually in GitHub Actions.

## Non-Goals

- Per-commit lead time, other DORA metrics, and changes to the Render deployment process.

## Constraints

- The `enhancement` label identifies feature PRs, including historical feature PRs in scope.
- Maintainers initiate production deployments manually. Report runs read deployment history.
- Only deployments that successfully go live on the designated Render production service qualify.
- A PR's first successful production deployment determines window membership, including for PRs merged before the window. Use verified history from before the window when needed to distinguish a first live deployment from a redeploy.
- If a promotion rewrites history and obscures the original feature PRs, require maintainer-reviewed evidence identifying the PRs it carried.
- Keep credentials out of reports and logs. Fail with a sanitized diagnostic if the available evidence cannot establish the result.

## Known Touchpoints

Maintainers manually deploy the designated Render production service from `main`, and its full deployment history is available for verification. See the [Render configuration findings](../dora-deployment-frequency/repo-findings.md).

Pull requests into `staging` and `main` allow merge commits only.

All staging-to-main promotions in the production history used by the report used merge commits.

Git history confirms that the AI Research Assistant PR (#96) and the staging-to-main promotions in PRs #109, #112, #153, #167, and #173 used merge commits.

GitHub PR metadata supplies feature PR identities and merge timestamps. Git history and promotion provenance link feature PRs to deployed revisions. Render supplies the production deployment outcome, live timestamp, and deployed SHA.

## Open Questions

- None.

## Success Criteria

See [gherkin.feature](gherkin.feature).
