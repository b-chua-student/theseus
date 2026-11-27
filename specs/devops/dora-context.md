# DORA reporting context

Theseus uses Render production deployment history and GitHub pull request or incident evidence. Use each report’s own reporting window and evidence rules when comparing metrics.

| Report | What it measures |
| --- | --- |
| Deployment frequency | Successful production deployments and the intervals between them. |
| Feature PR merge-to-production lead time | Median elapsed time from an eligible feature PR merge to its first live deployment. |
| Change failure rate | The share of in-scope production deployments requiring immediate intervention. |
| Failed deployment recovery time | Elapsed time from confirmed degradation to verified restoration for recorded incidents. |
| Deployment rework rate | The share of verified production deployments that were unplanned corrective work, based on maintainer-confirmed incident evidence. |

See the [pipeline guide](../../docs/PIPELINE.md#dora-production-reporting) for workflow triggers and configuration, and [pipeline operations](../../docs/pipeline-operations.md) for evidence checks.
