# Brief: Track deployment rework rate

- ID: dora-deployment-rework-rate
- Owner: Unassigned
- Date: 2026-11-26
- Base SHA: `2d5fcca1e6753bf1829b35a36f8e82c05ff65e1d`

## Goal

Help maintainers see what share of production deployments are unplanned responses to production incidents.

## Users / Roles

- Maintainers review the deployment rework rate report.

## In Scope

- Let maintainers run a report on demand for the preceding 30 days in UTC.
- Show rework and production deployment counts and the rate when the evidence is complete and the production total is positive. Report verified empty periods and gaps in evidence explicitly.

## Non-Goals

- Changes to deployment operations or reporting for other metrics.

## Constraints

- Count each qualifying deployment once.
- Include all production deployments in the reporting period in the denominator.
- Use each deployment's production live time to assign it to the period. Include the window start and exclude the report start, regardless of when the incident began.
- Count rework when production history confirms the deployment went live and a maintainer confirms on the incident record that the specific deployment was an unplanned response. Incidents of any cause qualify.

## Known Touchpoints

- Production deployment history and incident records provide evidence. Hotfix labels and rollback records can identify candidates for review.

## Assumptions

- The ticket specifies no additional non-functional requirements.

## Open Questions

- None.

## Success Criteria

1. For a period with production deployments and complete evidence, the report displays the distinct qualifying deployment count, the total production deployment count, and the first count divided by the second as a percentage.
2. When multiple records refer to the same qualifying deployment, the report counts it once.
3. A maintainer can run the report on demand. It includes deployments that went live exactly 30 days before the run in UTC and excludes deployments that went live at or after the run start.
4. A verified empty period shows both counts as zero and **N/A — no production deployments**. A period with production deployments and complete evidence of zero rework shows **0%**.
5. When a gap could change either count, the report displays **Incomplete evidence** and omits the rate. When production history is complete, it displays the verified production total, confirmed rework count, and number awaiting review. When production history is incomplete, it marks the production total as unverified.

## Reference Links

- [Source ticket](../../../tickets/dora-deployment-rework-rate.md)
- [DORA metric definitions](https://dora.dev/guides/dora-metrics/)
