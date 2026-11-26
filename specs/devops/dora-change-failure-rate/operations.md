# Run and maintain the DORA change failure rate report

Run **DORA change failure rate** from the repository's Actions tab or open the run created after a pull request merges into `main`. The job summary uses UTC. Both workflows use `RENDER_API_KEY`, `DORA_RENDER_SERVICE_ID` and `DORA_RENDER_FIRST_DEPLOY_ID` from the existing Render evidence configuration.

**Reconcile DORA production incidents** runs hourly. Each scan walks verified production history in live-time order to reconstruct which hotfix PRs have already shipped. GitHub issue entries persist corrective deployment IDs across scans. After an interrupted scan, the writer skips committed entries and continues with the remaining deployments. The report checks for corrective deployments whose entries are still missing.

## Link an existing incident

- In the original hotfix PR body, use a line such as `Incident: #123` or `Incident: https://github.com/OWNER/REPO/issues/123`. Apply `production-hotfix` to that PR.
- For a rollback, a repository maintainer can add `DORA rollback: dep-EXAMPLE` to the incident issue body or a comment before reconciliation. Use the corrective deploy ID from Render.

## Confirm attribution

Add a comment to the incident issue with one line per corrective deployment. Use the Render production service ID, the corrective deploy ID shown in the incident entry, the original deploy ID that caused the incident, and the actual intervention start time with a UTC offset. Repository write or admin permission is required for attribution. A subsequent attribution comment for the same corrective deployment on that issue supersedes the previous one.

```text
DORA attribution: {"service":"srv-example","corrective":"dep-corrective","original":"dep-original","status":"confirmed","caused":true,"type":"rollback","started":"2026-11-24T11:00:00Z","link":"https://dashboard.render.com/web/srv-example/deploys/dep-corrective"}
```

For a hotfix, use `"type":"hotfix"` and the URL of the original hotfix PR. While attribution is pending, a maintainer can provide a known start time or known original deploy ID with `"status":"pending"`. Omit fields that are still unknown. The report identifies pending issues whose confirmation could change the count.

## Review staging promotions

If squash or rebase removes the Git ancestry of the original staging PRs, commit a maintainer-reviewed `promotions.json` in this directory. Map the full promotion merge SHA to all original staging hotfix PR numbers shipped by that promotion. Use an empty array for a reviewed promotion with no hotfix PRs.

```json
{"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa": [123, 125]}
```
