# Theseus pipeline

## Continuous integration

[CI](../.github/workflows/ci.yml) runs on pushes and pull requests. Its two jobs run independently on GitHub-hosted Ubuntu runners.

| Job | Runtime | Checks |
| --- | --- | --- |
| Frontend | Node.js 24 | Install locked dependencies with `npm ci`, run ESLint and `svelte-check`, and build the production frontend. |
| Backend | Python 3.12 | Install development dependencies, run the Ruff lint and formatting hooks and the mypy hook, then run pytest. The Flask smoke tests cover app creation and the JSON response from `/api/health`. |

Open the pull request’s **Checks** tab or the workflow run under **Actions** to inspect failures. Expand the failed step for command output.

## Intake and Gherkin validation

[Intake and Gherkin validation](../.github/workflows/check-intake-gherkin.yaml) runs on pull requests that change `specs/*/*/brief.md` or `specs/*/*/gherkin.feature`.

- `changes` identifies affected files and Gherkin contexts.
- `intake` checks changed briefs for required headings, unresolved `TBD` or `TODO` placeholders, and an 80-line limit.
- `gherkin` lints changed feature files, compares scenario and `@S-###` tag counts, and checks for duplicate scenario IDs within each affected context.
- `summary` passes when `changes` succeeds and each validation job succeeds or is skipped. On pull requests outside the path filter, the workflow does not run.

## Deployment and recovery

The [Dockerfile](../Dockerfile) builds the Svelte frontend and packages it with the Flask backend. The [Docker image workflow](../.github/workflows/docker.yml) builds the image on pushes, pull requests, and manual dispatch.

### Failed deployment recovery time

Run [DORA failed deployment recovery time](../.github/workflows/dora-failed-deployment-recovery-time.yml) from **Actions → Run workflow**. Open the run’s job summary for the UTC run time, per-incident durations or statuses, median completed recovery time, and counts of completed, unresolved, and restored incidents with a missing timestamp.

The workflow reads open and closed issues labelled `dora-recovery-incident` across all recorded dates. Use the [production incident template](../.github/ISSUE_TEMPLATE/production-incident.md) to record maintainer confirmation, degradation and restoration evidence, and any corrective deployment links. Add recovery evidence to the original incident issue when a correction is already recorded elsewhere.

The report uses the workflow’s GitHub token and repository identifier. For Render Live evidence, it reads the maintainer-confirmed timestamp from the incident. If label lookup or incident loading fails, the summary marks the evidence as incomplete. A successful run with no completed durations displays “No completed recoveries with known timestamps.”

### Planned deployment and recovery work

- Build and start the container in CI, then smoke-test `/api/health`, `/`, and the frontend assets.
- Choose and document the production host, configure secrets, and deploy the tested image after CI passes on `main`.
- Verify the public health endpoint and frontend after each deploy. Record the commit SHA, image digest, UTC timestamp, and outcome. Send an alert on failure.
- Retain the previous known-good image, add exact rollback commands here, and record the recovery time from a rehearsal. Configure an external uptime check on `/api/health`.
- Add migration, backup, and restore verification when persistent storage is introduced.
