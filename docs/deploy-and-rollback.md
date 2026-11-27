# Deploy and rollback runbook

The production service is tracked through Render deployment history. Confirm its public URL, linked repository, deployment branch, auto-deploy condition, and owner in Render before release. Confirm required CI checks and one teammate approval in the GitHub rules for `main`.

## Release a change

1. Open a PR, review the changes and any data compatibility risks, and wait for required checks and teammate approval.
2. Merge into `main` and record the SHA. Follow that SHA through GitHub Actions and Render Events. Confirm whether the hosting service builds after CI passes. The GitHub Docker workflow builds an image for validation.
3. Check the Render logs for build, startup, and database or index errors. The repository has no dedicated migration workflow. For any data change, document ordering, backup, and compatibility before merging.
4. Check liveness with `curl --fail-with-body "$THESEUS_BASE_URL/api/health"` and expect HTTP 200 with `{"status":"ok"}`. Open the UI, sign in with a smoke-test account, and verify a disposable project and manuscript. Check persistence after reloading. For AI changes, use a single synthetic query against a prepared source.
5. Record the live SHA, deploy ID, timings, and smoke results in the team release channel or PR. For the course release, tag the verified SHA as `v1.0.0` and publish the [changelog](../CHANGELOG.md) with the production URL.

## Restore a known-good release

1. Record the failing deploy and symptoms in the [incident log](incident-log.md). Start timing at confirmed degradation and coordinate with the production owner.
2. In Render, identify the previous verified deployment by ID and SHA. Confirm compatibility with current data, indexes, and configuration before selecting its rollback action. If rollback is unavailable, coordinate a reviewed revert through the normal pipeline.
3. Watch the replacement deployment and repeat liveness, sign-in, and the affected workflow checks. Record the restored SHA, live timestamp, and first successful verification.
4. Check the auto-deploy setting after recovery. Coordinate the corrective PR with the production owner before normal release activity resumes.
5. Reconcile the incident using [pipeline operations](pipeline-operations.md).

## Rehearsal record

Record the environment, date, original SHA, restored SHA, deployment links, elapsed time, operator, and smoke results. A rehearsal has yet to be verified.
