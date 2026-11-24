## GitHub Actions repository configuration keys

| Configuration key | Purpose |
| --- | --- |
| Secret `RENDER_API_KEY` | Render API credential with access to read production deployment history |
| Variable `DORA_RENDER_SERVICE_ID` | ID of the Git-backed production service that deploys these revisions from `main` |
| Variable `DORA_RENDER_FIRST_DEPLOY_ID` | ID of the service's first deployment, including failed attempts, verified independently against the service's history. Use `empty` only for a verified never-deployed service and replace it with the first deployment ID when one exists. |
| Variable `DORA_FEATURE_LABEL` | Maintainer-approved GitHub label identifying every feature PR in scope, including historical PRs |

