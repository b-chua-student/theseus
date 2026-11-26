# Theseus pipeline

## Continuous integration

[CI](../.github/workflows/ci.yml) runs on pushes and pull requests. Its two jobs run independently on GitHub-hosted Ubuntu runners.

| Job | Runtime | Checks |
| --- | --- | --- |
| Frontend | Node.js 24 | Install locked dependencies, run ESLint and `svelte-check`, run unit and component tests, and build the production frontend. |
| Backend | Python 3.12 and Node.js 24 | Run the Ruff lint and formatting hooks and the mypy hook, run pytest unit and integration suites, then run Playwright end-to-end tests in Chromium. |

Open the pull request’s **Checks** tab or the workflow run under **Actions** to inspect failures. Expand the failed step for command output.

## Specification validation

[Intake and Gherkin validation](../.github/workflows/check-intake-gherkin.yaml) runs on pull requests that change `specs/*/*/brief.md` or `specs/*/*/gherkin.feature`.

- `changes` identifies affected files and Gherkin contexts.
- `intake` checks changed briefs for required headings, unresolved `TBD` or `TODO` placeholders, and an 80-line limit.
- `gherkin` lints changed feature files, compares scenario and `@S-###` tag counts, and checks for duplicate scenario IDs within each affected context.
- `summary` passes when `changes` succeeds and each validation job succeeds or is skipped. On pull requests outside the path filter, the workflow does not run.

[Spec file validation](../.github/workflows/check-spec-files.yaml) runs on pull requests that change `requirements.md`, `design.md`, or `tasks.md` under `specs/*/*/`. It checks affected feature specs for template structure, ticket and scenario traceability, and consistency between task dependencies, waves, and the Mermaid graph.

## Docker image build

The [Dockerfile](../Dockerfile) builds the Svelte frontend and packages it with the Flask backend. The [Docker image workflow](../.github/workflows/docker.yml) builds the image on pushes, pull requests, and manual dispatch.

### Failed deployment recovery time

Run [DORA failed deployment recovery time](../.github/workflows/dora-failed-deployment-recovery-time.yml) from **Actions → Run workflow**. Open the run’s job summary for the UTC run time, per-incident durations or statuses, median completed recovery time, and counts of completed, unresolved, and restored incidents with a missing timestamp.

The workflow reads open and closed issues labelled `dora-recovery-incident` across all recorded dates. Use the [production incident template](../.github/ISSUE_TEMPLATE/production-incident.md) to record maintainer confirmation, degradation and restoration evidence, and any corrective deployment links. Add recovery evidence to the original incident issue when a correction is already recorded elsewhere.

The report uses the workflow’s GitHub token and repository identifier. For Render Live evidence, it reads the maintainer-confirmed timestamp from the incident. If label lookup or incident loading fails, the summary marks the evidence as incomplete. A successful run with no completed durations displays “No completed recoveries with known timestamps.”

### Planned deployment and recovery work

The [Docker image workflow](../.github/workflows/docker.yml) runs on pushes, pull requests, and manual dispatch. It builds the [Dockerfile](../Dockerfile), which packages the Svelte frontend with the Flask backend, and tags the image locally as `theseus:<commit SHA>`. Its only job is the image build.

## DORA production reporting

The DORA workflows read deployment history for the Render production service. Configure the `RENDER_API_KEY` repository secret and the `DORA_RENDER_SERVICE_ID` and `DORA_RENDER_FIRST_DEPLOY_ID` repository variables. The first deploy ID anchors the history to the service's earliest deployment attempt, including failed attempts.

| Workflow | Trigger | Output |
| --- | --- | --- |
| [Deployment frequency](../.github/workflows/dora-deployment-frequency.yml) | PR merged into `main` | Publishes deployment frequency to the job summary. |
| [Feature PR merge-to-production lead time](../.github/workflows/dora-lead-time.yml) | Manual dispatch or Sunday at 00:00 Manila time when `DORA_WEEKLY_ENABLED` is `true` | Publishes median time from feature PR merge to first live deployment. `DORA_FEATURE_LABEL` identifies feature PRs. |
| [Change failure rate](../.github/workflows/dora-change-failure-rate.yml) | PR merged into `main` or manual dispatch | Publishes the change failure rate and flags pending incident attribution in the job summary. |
| [Production incident reconciliation](../.github/workflows/dora-production-incidents.yml) | Hourly at minute 17 | Creates or updates GitHub issues for detected production rollbacks and hotfixes. |

For configuration and verification steps, see the [lead time runbook](../specs/devops/dora-change-lead-time/operations.md) and the [change failure rate runbook](../specs/devops/dora-change-failure-rate/operations.md).
