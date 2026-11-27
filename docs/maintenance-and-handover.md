# Maintenance and handover

| Responsibility | Where to work | Cadence |
| --- | --- | --- |
| Delivery and alerts | GitHub checks, Render deployment events, uptime monitor | After each deployment and at each consultation |
| Dependency and secret review | Package lockfiles, Python requirements, CI and hosting secret stores | Each sprint and after a security advisory |
| AI model, prompt, and budget review | Assistant settings, RAG tests, provider usage dashboard | Before model or prompt changes and at each consultation |
| Database and vectors | MongoDB backups, Chroma storage, retrieval smoke checks | Before data changes and during scheduled restore drills |

Confirm the service owner, backup operator, escalation channel, production and preview URLs, monitor, and backup schedule during handover. Grant access through the hosting and repository platforms. Keep secret values out of shared notes.

Set separate database names, session keys, OAuth callbacks, and provider keys for each hosted environment. Apply provider budgets and alerts where supported. Rotate credentials in the secret store, deploy the replacement, verify it, then revoke the old credentials. Track the owner and completion date.

For a backup drill, restore into an isolated database, verify sign-in and sample manuscript and revision reads, and test retrieval with the matching vector snapshot or a controlled reindex. Record backup age, elapsed time, and validation results. Inspect the effect of model changes on existing vectors before reindexing.

For an AI incident, check provider status, recent model changes, request errors, and budget. Removing `GEMINI_API_KEY` with a restart takes Gemini out of the default application wiring. Verify fallback behavior in a preview service before relying on this mitigation. A production runtime kill switch is unverified. See the [release runbook](deploy-and-rollback.md).
