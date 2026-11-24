# Running the lead time report

The [GitHub Actions workflow](../../../.github/workflows/dora-lead-time.yml) publishes
the report to its job summary. Use **Run workflow** to generate a manual report.
The weekly report is scheduled for Sunday at 00:00 Manila time (Saturday at
16:00 UTC). Confirm the job summary as the publication surface before enabling
the weekly run.

## Production evidence to confirm

| Repository setting | Value to confirm |
| --- | --- |
| Secret `RENDER_API_KEY` | Render API credential with access to read production deployment history |
| Variable `DORA_RENDER_SERVICE_ID` | ID of the Git-backed production service that deploys these revisions from `main` |
| Variable `DORA_RENDER_FIRST_DEPLOY_ID` | ID of the service's first deployment, including failed attempts, verified independently against the service's history. Use `empty` only for a verified never-deployed service and replace it with the first deployment ID when one exists. |
| Variable `DORA_FEATURE_LABEL` | Maintainer-approved GitHub label identifying every feature PR in scope, including historical PRs |
| Variable `DORA_WEEKLY_ENABLED` | Set to `true` only after recording maintainer verification of the manual report |

Confirm that Render exposes uninterrupted history from the service's first
deployment, that `live` and `deactivated` records represent successful deployments,
and that `finishedAt` retains the original live timestamp after deactivation and
rollback. Validate these assumptions against production records. The script checks
pagination, required fields, and the first deployment anchor. The anchor detects a
truncated beginning. Only an independent history check can establish that the
provider retained every record between the first and last deployment. If the
production service was replaced, establish that the selected history covers first
deployments across the transition before relying on these reports. This implementation
reads a single service history. [Render deploy API](https://api-docs.render.com/reference/list-deploys)

Confirm that the deployed Git revisions are available from the repository and that
the GitHub feature labels and merged PR metadata cover their history. The script
identifies standard promotion PRs by a same-repository `staging` head and a
`main` base. A two-parent promotion uses Git reachability. Direct feature PRs use
their GitHub merge revision, which supports merge commits and squash merges.
A rebased feature PR can use its final commit when production deploys the feature
as a unit. Confirm whether rebases are permitted and that production never deploys
a partial rebase. Confirm that historical rewrites which carried staging features
are identifiable as promotion PRs. [GitHub pull request merge revision semantics](https://docs.github.com/en/rest/pulls/pulls#get-a-pull-request)

For each rewritten promotion, add a maintainer-reviewed
`specs/devops/dora-change-lead-time/promotions.json` entry. Use the full GitHub
merge commit SHA of the PR into `main` as the key and the complete list of original
feature PR numbers merged into `staging` as its value. An empty list asserts that
the promotion carried zero feature PRs. Derive each list from retained promotion
records or a verified review of the promoted changes and record the supporting
evidence in the manifest change's PR. This also identifies promotions from a
nonstandard head branch. The script rejects a deployed standard promotion with
a rewritten history and no matching entry. It relies on maintainers to confirm
the completeness of the promotion records, including any historical rewrites
outside the standard branch flow.

## Verification and activation

1. Confirm the settings and historical evidence above. Record the confirmed
   values and coverage in the verification record, omitting credentials.
2. Run the manual workflow from GitHub Actions. Compare the UTC window, count,
   and median against GitHub and Render. Expand the summary's PR-to-deployment
   evidence and sample PRs across the merge strategies used in production.
   Check each original merge time, the deployed revision, and its first live time.
3. Record the verified run URL and maintainer sign-off in this spec. Confirm the
   first scheduled run with weekly publication disabled has a skipped report job.
4. After verification, set `DORA_WEEKLY_ENABLED` to `true` and confirm the next
   scheduled run publishes a summary with a fresh UTC window.

The production evidence and publication surface are pending maintainer confirmation.
No verified run has been recorded.
