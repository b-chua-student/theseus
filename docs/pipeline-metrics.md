# Weekly pipeline metrics

Use the actual consultation windows and record their date ranges and time zone. Link the source runs and deployment records for each row.

| Week | Avg PR pipeline time (min) | Main pipeline time (min) | Pipeline success rate (%) | Production deploys | Avg lead time, merge to live (min) | Failed deploys | Time to recover (min) | Change made this week |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sprint 1 | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| Sprint 2 | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| Sprint 3 | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| Sprint 4 | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| [DORA snapshot, Oct 28–Nov 27, 2026 UTC](#dora-metrics-report) | Pending | Pending | Pending | 11 | Mean pending (DORA median: 236.4 min) | Pending | No completed recoveries | Pending |

The snapshot dates use the DORA lead-time and rework reporting window. The snapshot’s production deploy count comes from the rework section. The deployment frequency section covers verified service history. The change failure rate uses its own window and counts deployments requiring immediate intervention. The weekly failed-deployment count requires Render attempt history. Sprint rows require confirmed consultation dates and source records.

Use one duration per completed CI run. Record the mean of completed main CI runs for the window and note the sample count. For success rate, divide successful runs by completed runs with a success or failure outcome and report cancellations separately. Count live and failed production attempts using Render history. Match reviewed merges to their first live deployment and take the arithmetic mean of matched durations. Report missing matches. For recovery, link incident evidence and give the time from degradation to verified restoration for each completed incident. Record zero only where evidence supports it.

Use [pipeline operations](pipeline-operations.md) for the DORA reports and [optimization log](pipeline-optimization.md) for timing comparisons.

## DORA metrics report

Generated at 2026-11-27 14:24:16 UTC. [GitHub Actions report run](https://github.com/b-chua-student/theseus/actions/runs/46015434857)

### Deployment frequency

Successful production deployments: **11**

Intervals between successful production deployments, in report order:

| Interval | Elapsed time |
| --- | --- |
| 1 | 3 minutes, 30.54241 seconds |
| 2 | 2 minutes, 36.208572 seconds |
| 3 | 1 hour, 40 minutes, 10.698498 seconds |
| 4 | 3 days, 15 hours, 17 minutes, 53.819416 seconds |
| 5 | 1 day, 6 hours, 13 minutes, 15.740073 seconds |
| 6 | 1 day, 48 minutes, 34.731525 seconds |
| 7 | 17 hours, 16 minutes, 35.312137 seconds |
| 8 | 2 hours, 17 minutes, 32.604903 seconds |
| 9 | 1 hour, 16 minutes, 14.170999 seconds |
| 10 | 5 hours, 8 minutes, 53.846118 seconds |

### Feature PR merge-to-production lead time

Window (UTC): `2026-10-28T14:24:16+00:00` to `2026-11-27T14:24:16+00:00`

- Included feature PRs: 4
- Median lead time: **3.94 hours**
- PR-to-deployment evidence: No entries supplied in the report.

### Change failure rate

- Window start (UTC): `2026-10-27T14:24:16+00:00`
- Window cutoff (UTC): `2026-11-26T14:24:16+00:00`
- Deployments requiring immediate intervention: 0
- Total production deployments: 7
- Change failure rate: **0%**

### Failed deployment recovery time

- Completed recoveries: 0
- Unresolved failures: 0
- Restored failures with a missing timestamp: 0

No completed recoveries with known timestamps.

### Deployment rework rate

- Window start (UTC): `2026-10-28T14:24:16+00:00`
- Window end (UTC, exclusive): `2026-11-27T14:24:16+00:00`
- Rework deployments: 0
- Production deployments: 11
- Deployment rework rate: **0%**
