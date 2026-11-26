# Requirements — Track DORA change failure rate

- Ticket: `tickets/dora-change-failure-rate.md`

## Requirements

| ID | Requirement | Source | Ticket lines | Scenarios |
| --- | --- | --- | --- | --- |
| R-001 | Use Render production deployment history for the total. With complete evidence and a nonzero total, show the intervention count, total, and intervention count divided by the total as a percentage. | from ticket | 12, 17, 27 | S-028, S-029, S-030, S-036, S-040, S-041 |
| R-002 | Let a maintainer start a report on demand. | from ticket | 13, 21 | S-031, S-036 |
| R-003 | Start a report automatically for each merge into main. | from ticket | 13, 22 | S-032, S-036 |
| R-004 | For both triggers, display both bounds of the rolling 30-day window ending 24 hours before the run starts. Include production deployments whose live times are strictly after the start and at or before the cutoff. | from ticket | 20 | S-036, S-040 |
| R-005 | Count an intervention only if a maintainer-confirmed incident record confirms causation and supplies the original Render deploy ID, intervention type and start time, and link to the rollback deploy or hotfix pull request. | from ticket | 28, 32 | S-028, S-029, S-033 |
| R-006 | Count an intervention that starts within 24 hours of the original deployment going live, including exactly 24 hours. Attribute it to the original deployment's reporting period and count each qualifying original deployment once. | from ticket | 29, 31 | S-028, S-029, S-033, S-036 |
| R-007 | When production history confirms an empty period, show zero for both counts and mark the rate unavailable. | from ticket | 18 | S-034 |
| R-008 | When evidence is incomplete, mark the rate unavailable, identify the missing evidence, and label any displayed counts as confirmed so far. | from ticket | 19 | S-035 |
| R-009 | Identify a pending incident as missing evidence if confirmation could add an eligible deployment to the intervention count under the 24-hour rule. If it cannot change the count, publish the rate when at least one deployment is eligible and all other evidence is complete. | from ticket | 30 | S-035, S-041 |
| R-010 | When a production rollback or qualifying hotfix goes live, create a GitHub incident issue or update the explicitly linked incident issue. Record the corrective action link and mark original deployment attribution pending maintainer confirmation. Use the original hotfix pull request's issue link when present. | from ticket | 14, 23, 32, 34 | S-037, S-038 |
| R-011 | Recognize a hotfix by the `production-hotfix` label on its original pull request into main or staging. Recognize a staging hotfix when it reaches production through an unlabeled promotion into main. | from ticket | 14, 33 | S-037, S-038 |
| R-012 | Record each qualifying corrective deployment on one incident issue. Reprocessing creates neither a second issue nor a duplicate entry. | from ticket | 23, 24 | S-039 |

## Open Questions

- None.
