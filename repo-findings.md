# Repository findings

Theseus ships a Svelte manuscript editor and Flask API in one deployable container. For the supported development commands, start with the [README](README.md#local-setup).

| Area | Where to look |
| --- | --- |
| Application structure | [Architecture](docs/architecture.md) and the [Flask application factory](backend/bootstrap/app.py) |
| Browser and API contracts | [Frontend setup](frontend/README.md), [API reference](docs/api.md), and the [frontend API clients](frontend/src/lib/api) |
| Local data and assistant checks | [Reviewer setup](docs/local-setup.md) and [assistant evaluation evidence](docs/ai-feature.md) |
| Feature specifications | [Repository workflow](AGENTS.md), [tickets](tickets), and [feature specs](specs) |
| Delivery and reporting | [CI and DORA workflows](docs/PIPELINE.md), [pipeline operations](docs/pipeline-operations.md), and the [release runbook](docs/deploy-and-rollback.md) |

## GitHub Actions repository configuration keys

| Configuration key | Purpose |
| --- | --- |
| Secret `RENDER_API_KEY` | Render API credential with access to read production deployment history |
| Variable `DORA_RENDER_SERVICE_ID` | ID of the Git-backed production service that deploys these revisions from `main` |
| Variable `DORA_RENDER_FIRST_DEPLOY_ID` | ID of the service's first deployment, including failed attempts, verified independently against the service's history. Use `empty` only for a verified never-deployed service and replace it with the first deployment ID when one exists. |
| Variable `DORA_FEATURE_LABEL` | Maintainer-approved GitHub label identifying every feature PR in scope, including historical PRs |
