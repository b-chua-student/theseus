# Brief: Track DORA change failure rate

- ID: #158
- Owner: @b-chua-student
- Date: 2026-11-25
- Base SHA: `42095acc46395ed47151ec80a962ab31e548d456`

## Goal

Show Theseus maintainers how often production deployments require immediate intervention.

## Users / Roles

- Theseus maintainers review the change failure rate report.

## In Scope

- Report the percentage of production deployments that require immediate intervention, such as a rollback or hotfix.
- Let maintainers run the report on demand and run it automatically after each merge into main.
- Automatically create a GitHub incident issue when a production rollback or a hotfix from a pull request labeled `production-hotfix` goes live. Update an explicitly linked incident issue when one exists.

## Non-Goals

- Changes to deployment operations.
- Reporting for other metrics.

## Constraints

- Use Render production deployment history for the total.
- Count an intervention only when a maintainer-confirmed incident record states that the original deployment caused the issue and includes its Render deploy ID, the intervention type and start time, and a link to the rollback deployment or hotfix pull request.
- An intervention qualifies if it starts within 24 hours of the original deployment going live, including exactly 24 hours. Attribute it to the original deployment's reporting period.
- Count each qualifying original deployment once, even if it requires several interventions.
- For both triggers, include only deployments within the reporting period that went live at or before the cutoff, 24 hours before the run starts.
- Record each qualifying corrective deployment on one issue, even if it is processed more than once.
- Automated issue entries link to the corrective action and mark attribution pending until a maintainer confirms the original deployment.
- Apply `production-hotfix` to the original hotfix pull request into `staging` or `main`. Use that pull request to link an existing incident issue, when available.

## Known Touchpoints

- The Theseus DevOps requirements call for tracking change failure rate.
- Render is the production deployment platform and the source of production deployment history.
- GitHub incident issues record corrective deployments and maintainer-confirmed attribution.

## Assumptions

- None recorded in the ticket.

## Open Questions

- None.

## Success Criteria

1. With complete evidence and at least one production deployment, the report shows the count requiring immediate intervention, the total production deployment count, and the intervention count as a percentage of the total.
2. A production deployment requiring multiple immediate interventions contributes one to the intervention count.
3. A maintainer can start a change failure rate report on demand.
4. Each merge into main starts a change failure rate report automatically.
5. The report attributes each confirmed intervention starting within 24 hours to the original deployment's reporting period.
6. When production history confirms there were no deployments, the report shows zero for both counts and marks the rate unavailable.
7. When evidence is incomplete, the report marks the rate unavailable, identifies what is missing, and labels any displayed counts as confirmed so far.
8. Manual and automatic reports display the cutoff and include eligible deployments through that cutoff.
9. A qualifying corrective deployment creates a GitHub incident issue or updates its explicitly linked incident issue with the corrective action link and pending attribution.
10. Reprocessing a qualifying corrective deployment leaves one incident issue entry for that deployment.
11. A labeled hotfix merged into staging is recorded when it goes live in production after an unlabeled promotion into main. A labeled hotfix merged directly into main is also recorded when it goes live in production.

## Reference Links

- [GitHub issue #158](https://github.com/b-chua-student/theseus/issues/158)
- [Local ticket for issue #158](../../../tickets/dora-change-failure-rate.md)
- [DORA metric definitions](https://dora.dev/guides/dora-metrics/)
