# Brief: Report feature PR merge-to-production lead time

- Origin: issue #140
- Scope: trace merged feature PRs through staging to production.

## Goal

Give Theseus maintainers a baseline for how long a merged feature PR takes to go live in production.

## In Scope

- Trace feature PRs merged into `staging` through their promotion to `main`, and trace feature PRs merged directly into `main`.
- Measure one sample per feature PR from its merge timestamp to its first successful production deployment. A promotion can carry multiple feature PRs, each with its own merge timestamp.
- Report the UTC bounds of a rolling 30-day window, median lead time in hours, and included PR count on demand in GitHub Actions. Publish weekly after maintainer verification.

## Non-Goals

- Per-commit lead time, other DORA metrics, and changes to the Render deployment process.

## Constraints

- Only deployments that successfully go live on the designated Render production service qualify.
- A PR's first successful production deployment determines window membership, including for PRs merged before the window.
- Keep credentials out of reports and logs. Fail with a sanitized diagnostic if the available evidence cannot establish the result.

## Known Touchpoints

GitHub PR metadata supplies feature PR identities and merge timestamps. Git history and promotion provenance link feature PRs to deployed revisions. Render supplies the production deployment outcome, live timestamp, and deployed SHA.

## Open Questions

- Which Render service is production, and how far back can its deployment history be verified?
- Which merge strategies are enabled on `staging` and `main`, and what evidence links feature PRs to the deployed revision when history is rewritten?

## Success Criteria

See [lead-time.feature](lead-time.feature).
