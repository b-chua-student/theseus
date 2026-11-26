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
- Add a **Deployment rework** section to the production incident template to guide maintainer confirmation.

## Non-Goals

- Changes to deployment operations or reporting for other metrics.

## Constraints

- Count each qualifying deployment once.
- Include all production deployments in the reporting period in the denominator.
- Use each deployment's production live time to assign it to the period. Include the window start and exclude the report start, regardless of when the incident began.
- Count rework when production history confirms the deployment went live and a maintainer confirms on the incident record that the specific deployment was an unplanned response. Incidents of any cause qualify.
- A maintainer reviews each production deployment by ID. Accept either valid incident confirmation or an explicit reviewed disposition of no qualifying rework. Deployments without either disposition remain awaiting review, including those without linked incidents.

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

6. A deployment with no linked incident or recorded disposition contributes to the awaiting-review count. When every deployment has a valid disposition and the rest of the evidence is complete, the report shows the rate.
7. The production incident template includes a **Deployment rework** section that explains how a maintainer records that a specific deployment went live in production as an unplanned response to the incident.

## Reference Links

- [Source ticket](../../../tickets/dora-deployment-rework-rate.md)
- [DORA metric definitions](https://dora.dev/guides/dora-metrics/)
