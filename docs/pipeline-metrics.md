# Weekly pipeline metrics

Use the actual consultation windows and record their date ranges and time zone. Link the source runs and deployment records for each row.

| Week | Avg PR pipeline time (min) | Main pipeline time (min) | Pipeline success rate (%) | Production deploys | Avg lead time, merge to live (min) | Failed deploys | Time to recover (min) | Change made this week |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sprint 1 | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| Sprint 2 | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| Sprint 3 | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| Sprint 4 | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |

Use one duration per completed CI run. Record the mean of completed main CI runs for the window and note the sample count. For success rate, divide successful runs by completed runs with a success or failure outcome and report cancellations separately. Count live and failed production attempts using Render history. Match reviewed merges to their first live deployment and take the arithmetic mean of matched durations. Report missing matches. For recovery, link incident evidence and give the time from degradation to verified restoration for each completed incident. Record zero only where evidence supports it.

Use [pipeline operations](pipeline-operations.md) for the DORA reports and [optimization log](pipeline-optimization.md) for timing comparisons.
