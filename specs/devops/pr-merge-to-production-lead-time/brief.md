# Brief: Report PR merge-to-production lead time

- ID: #140 (pr-merge-to-production-lead-time)
- Owner: Unspecified in ticket
- Date: 2026-11-23
- Base SHA: b3425fba1bba40273e9bc63cfb23a5d681f60e2a

## Goal

Give Theseus maintainers a baseline for how long merged pull requests take to reach users in production.

## Users / Roles

- Theseus maintainer

## In Scope

- `from ticket` (Scope, first bullet) Measure elapsed time from each pull request's merge into the production branch to the first successful production deployment containing its changes.
- `from ticket` (Scope, second bullet) Make the report available on demand in GitHub Actions and publish it weekly once the results are verified.
- `from ticket` (Scope, third bullet) Report the period, median lead time, and included pull request count for a rolling 30-day window.

## Non-Goals

- Other DORA metrics and PR-open-to-production lead time.
- Changes to the existing Render deployment process.

## Constraints

- `from ticket` (Rules / Constraints, first bullet) Include a pull request when its first successful production deployment falls within the reporting window, even if it merged earlier.
- `from ticket` (Rules / Constraints, second bullet) Exclude preview, staging, and unsuccessful deployments.
- `from ticket` (Rules / Constraints, third bullet) Label the result “PR merge-to-production lead time.”
- `from ticket` (Non-Functional Requirements) Keep credentials out of report output and logs.

## Known Touchpoints

- Render is identified in the ticket as the hosting platform. GitHub Actions is identified as the on-demand reporting touchpoint.

## Assumptions

- None supplied.

## Open Questions

- Which Render service and branch should be treated as production? Deferred: the ticket leaves these identifiers open.

## Success Criteria

1. `from ticket` (Scope, second and third bullets, and Rules / Constraints, third bullet) A maintainer can request the report in GitHub Actions and see the “PR merge-to-production lead time” label, rolling 30-day reporting period, median lead time, and included pull request count.
2. `from ticket` (Scope, second bullet) The report is published weekly once its results are verified.
3. `from ticket` (Scope, first bullet, and Expected Outcomes, first checkbox) A deployment that ships several pull requests contributes one sample per pull request, based on its own merge time into the production branch.
4. `from ticket` (Expected Outcomes, second checkbox) A merged pull request contributes neither to the count nor to the median until it successfully ships to production.
5. `from ticket` (Expected Outcomes, third checkbox) A redeploy preserves the first successful production deployment time and adds no second sample.
6. `from ticket` (Expected Outcomes, fourth checkbox) An empty period shows zero included pull requests and an unavailable median.
7. `from ticket` (Rules / Constraints, first bullet) A pull request merged before the window opened is included when its first successful production deployment falls within the window.
8. `from ticket` (Rules / Constraints, second bullet) Preview, staging, and unsuccessful deployments contribute no samples.
9. `from ticket` (Non-Functional Requirements) Credentials are absent from the report output and its logs.

## Reference Links

- [GitHub issue #140](https://github.com/b-chua-student/theseus/issues/140)
