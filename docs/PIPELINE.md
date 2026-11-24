# Theseus pipeline

## Continuous integration

[CI](.github/workflows/ci.yml) runs on pushes and pull requests. Its two jobs run independently on GitHub-hosted Ubuntu runners.

| Job | Runtime | Checks |
| --- | --- | --- |
| Frontend | Node.js 24 | Install locked dependencies with `npm ci`, run ESLint and `svelte-check`, and build the production frontend. |
| Backend | Python 3.12 | Install development dependencies, run the Ruff lint and formatting hooks and the mypy hook, then run pytest. The Flask smoke tests cover app creation and the JSON response from `/api/health`. |

Open the pull request’s **Checks** tab or the workflow run under **Actions** to inspect failures. Expand the failed step for command output.

## Intake and Gherkin validation

[Intake and Gherkin validation](.github/workflows/check-intake-gherkin.yaml) runs on pull requests that change `.kiro/specs/*/brief.md` or `.kiro/specs/*/*/*.feature`.

- `changes` identifies affected files and Gherkin contexts.
- `intake` checks changed briefs for required headings, unresolved `TBD` or `TODO` placeholders, and an 80-line limit.
- `gherkin` lints changed feature files, compares scenario and `@S-###` tag counts, and checks for duplicate scenario IDs within each affected context.
- `summary` passes when `changes` succeeds and each validation job succeeds or is skipped. On pull requests outside the path filter, the workflow does not run.

## Deployment and recovery

The [Dockerfile](Dockerfile) builds the Svelte frontend and packages it with the Flask backend. The current workflows run CI checks. Deployment and recovery work is planned.

- Build and start the container in CI, then smoke-test `/api/health`, `/`, and the frontend assets.
- Choose and document the production host, configure secrets, and deploy the tested image after CI passes on `main`.
- Verify the public health endpoint and frontend after each deploy. Record the commit SHA, image digest, UTC timestamp, and outcome. Send an alert on failure.
- Retain the previous known-good image, add exact rollback commands here, and record the recovery time from a rehearsal. Configure an external uptime check on `/api/health`.
- Add migration, backup, and restore verification when persistent storage is introduced.
