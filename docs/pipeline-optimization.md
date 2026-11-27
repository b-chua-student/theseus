# Pipeline optimization log

| Change visible in the repository | Before | After | Evidence and result |
| --- | --- | --- | --- |
| npm and pip dependency caching | Pending | Pending | Compare CI runs with equivalent workloads and record cache hits. |
| Cached MiniLM snapshot | Pending | Pending | Compare model preparation time and total backend job time for cache miss and hit. |
| Independent frontend and backend jobs | Pending | Pending | Measure elapsed workflow time and the duration of each job. |
| Path filters for specification workflows | Pending | Pending | Compare the runs triggered by spec-only and unrelated PRs. |

For each comparison, record the run links, revisions, sample count, runner, elapsed time, and conclusion. Use like-for-like workloads and label any cold-cache runs or retries. Existing configuration is visible in [CI](../.github/workflows/ci.yml) and the [spec checks](PIPELINE.md#specification-validation).
