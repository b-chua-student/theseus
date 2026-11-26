# Requirements — Track failed deployment recovery time

- Ticket: `tickets/dora-failed-deployment-recovery-time.md`

## Requirements

| ID | Requirement | Source | Ticket lines | Scenarios |
| --- | --- | --- | --- | --- |
| R-001 | Include a failure only when a deployment caused production degradation that required immediate intervention. Exclude nonqualifying failures and attempts from all entries, counts, and the median, including failed attempts that leave production healthy. | from ticket | 9, 15, 16 | S-048, S-051, S-056 |
| R-002 | For a restored qualifying failure with both timestamps known, show the elapsed time from the start of degradation to restoration of normal service. | from ticket | 9, 12 | S-049, S-050, S-054, S-055 |
| R-003 | Establish degradation and restoration times from production monitoring or a maintainer-confirmed timeline. Use a corrective deployment's Render Live time for restoration when evidence confirms recovery at that time. | from ticket | 13 | S-049, S-050, S-054, S-055 |
| R-004 | Let maintainers record a qualifying failure and see it in the report before any corrective deployment. Include recoveries confirmed by monitoring or a maintainer-confirmed timeline when service recovers without a corrective deployment. | from ticket | 14 | S-052, S-054, S-058 |
| R-005 | Record whether normal service has been restored independently of whether its restoration timestamp is known. | from ticket | 14 | S-052, S-053 |
| R-006 | Count each qualifying production incident once even when it has multiple corrective deployments. Each completed recovery with both timestamps contributes one duration to the median and one to the completed recovery count. | from ticket | 18 | S-055 |
| R-007 | Show the median of completed recovery durations and the number of durations included. Display “No completed recoveries with known timestamps.” when there are no eligible durations. | from ticket | 17 | S-046, S-047, S-048, S-051, S-053, S-055, S-056, S-057 |
| R-008 | Show unresolved incidents as “Unresolved” and restored incidents missing either or both timestamps as “Missing timestamp.” Leave both groups' durations blank, exclude them from the median, and show separate counts for them. | from ticket | 19 | S-046, S-047, S-052, S-053, S-058 |
| R-009 | With zero qualifying failures, show no incident entries, zero for all three counts, and “No completed recoveries with known timestamps.” | from ticket | 20 | S-056 |
| R-010 | Preserve deployment operations and reporting for other metrics. | from ticket | 36 | - |
| R-011 | Let maintainers refresh a dedicated recovery report on demand. Show the report run time in UTC and include all recorded qualifying incidents. | from ticket | 21 | S-059 |
| R-012 | Use the latest valid maintainer confirmation that explicitly resolves conflicting timeline evidence. Until resolved, treat a disputed timestamp as unknown. Treat a restoration time earlier than degradation as unknown until corrected. For restored incidents, apply the missing-timestamp rules and identify the incident and evidence problem. | from ticket | 22 | S-060, S-061 |
| R-013 | If incident records cannot be loaded, report incomplete evidence in place of the empty-report result. | from ticket | 23 | S-062 |
| R-014 | Keep one record per qualifying incident. Let maintainers confirm the incident independently of corrective deployments and associate subsequent corrective deployments with the same record. | from ticket | 24 | S-055, S-058 |

## Open Questions

- None.
