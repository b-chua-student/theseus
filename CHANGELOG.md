# Changelog

## v1.0.0 release candidate

- Edit project manuscripts and sections, save revisions, restore earlier versions, and work with draft branches.
- Manage sources and use manuscript and source context in writing-assistant conversations.
- Validate assistant answers against evidence, with structured status and timeout handling.
- Run frontend, backend, and browser checks in GitHub Actions and generate deployment evidence reports.

For persistent deployments, configure MongoDB and a stable Flask session key. Review vector persistence and indexing settings before changing the embedding model. See the [release runbook](docs/deploy-and-rollback.md) and [AI limitations](docs/ai-feature.md#evaluation-evidence).
