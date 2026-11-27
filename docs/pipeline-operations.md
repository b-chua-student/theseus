# Pipeline operations

See the [pipeline overview](PIPELINE.md) for workflow triggers, reporting periods, and configuration.

## Inspect CI and build runs

1. Open the pull request’s **Checks** tab or find the run under **Actions**.
2. Open the failed job and expand the first failed step to see the command output.

## Run and verify DORA reports

1. Open **Actions** and select the report. For a report that supports manual dispatch, select **Run workflow**. For deployment frequency, open the run triggered by a PR merge into `main`.
2. Open the job summary and check its reporting period and evidence status. If the job failed before publishing a summary, open the report step for the diagnostic.

Use the [lead time runbook](../specs/devops/dora-change-lead-time/operations.md) to verify feature PR provenance and run the report manually. Use the [change failure rate runbook](../specs/devops/dora-change-failure-rate/operations.md) to verify Render deployment evidence, reconcile corrective deployments, and record incident attribution.

## Record and verify recovery evidence

1. Use the original incident issue and apply the `dora-recovery-incident` label. Open and closed issues qualify for review across all recorded dates.
2. Record maintainer confirmation, degradation and restoration timestamps with UTC offsets, and any corrective deployment links. If a correction is recorded elsewhere, link it from the original incident issue. Follow the [production incident template](../.github/ISSUE_TEMPLATE/production-incident.md).
3. Run **DORA failed deployment recovery time** manually. Check the per-incident status and the counts of completed, unresolved, and restored incidents with missing timestamps.

The recovery workflow reads incident evidence using the workflow’s GitHub token. For Render Live evidence, it uses the maintainer-confirmed timestamp recorded on the incident. If label lookup or incident loading fails, the job summary marks the evidence as incomplete. When collection succeeds and no completed recoveries have known timestamps, the summary displays “No completed recoveries with known timestamps.”

## Verify scheduled reports and triage incidents

Open **Scheduled DORA metrics report** in Actions. Check the run's evidence warnings and download the `dora-report` artifact for the full report. Add the run link to the [weekly metrics log](pipeline-metrics.md) alongside the course-specific CI and lead-time calculations.

For a failed main build or production alert, record the failing run, live SHA, impact, and first observed time. Escalate to the production owner. Use the [deploy and rollback runbook](deploy-and-rollback.md) to verify recovery, then capture the cause and prevention in the [incident log](incident-log.md).
