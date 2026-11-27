# Requirements — Track deployment rework rate

- Ticket: `tickets/dora-deployment-rework-rate.md`

## Requirements

| ID | Requirement | Source | Ticket lines | Scenarios |
| --- | --- | --- | --- | --- |
| R-001 | Let a maintainer run the report on demand for the preceding 30 days in UTC. | from ticket | 13 | S-048 |
| R-002 | Assign deployments to the period by verified production live time. Include the window start and exclude the report start regardless of when the incident began. | from ticket | 21, 22 | S-048 |
| R-003 | Include every deployment that went live in production during the reporting period in the denominator. | from ticket | 20, 21, 22 | S-046, S-047, S-048, S-050, S-051, S-053 |
| R-004 | Count rework only when production history establishes that the deployment went live and a maintainer confirms on a production incident record that the specific deployment was an unplanned response. An incident can have any cause. | from ticket | 10, 21 | S-046, S-047, S-051 |
| R-005 | Count each qualifying corrective deployment once, even when multiple records refer to it. | from ticket | 20 | S-047 |
| R-006 | With complete evidence and a positive production total, show the rework count, the production deployment total, and the rework count divided by the total as a percentage. Show 0% when none qualify. | from ticket | 10, 14 | S-046, S-047, S-050, S-051, S-053 |
| R-007 | When verified production history shows an empty period, show zero for both counts and display **N/A — no production deployments** for the rate. | from ticket | 15 | S-049 |
| R-008 | When missing evidence could change either count, show **Incomplete evidence** and withhold the percentage. If production history is complete, show its verified total, the confirmed rework count, and the count of deployments affected by the evidence gap. If production history is incomplete, mark its total as unverified. | from ticket | 16 | S-052, S-055, S-056 |
| R-009 | With readable incident evidence, include deployments with no valid rework confirmation only in the production total. Publish the rate without a separate review or no-rework confirmation. | from ticket | 14, 23 | S-046, S-047, S-050, S-051, S-053 |
| R-010 | Include a **Deployment rework** section in the production incident template that explains how a maintainer records that a specific deployment went live in production as an unplanned response to the incident. | from ticket | 17 | S-054 |
| R-011 | Count each deployment whose rework status could change because incident evidence is unavailable. If the scope is unknown, include all deployments that could still be confirmed as rework. Retain valid confirmations that the gap cannot change. | from ticket | 24 | S-055, S-056 |

## Open Questions

- None.
