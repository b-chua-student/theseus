# Design — Track DORA change failure rate

## Design

| ID | Decision | Components | Requirements |
| --- | --- | --- | --- |
| D-001 | Use a dedicated GitHub Actions reporting workflow with manual dispatch and a merged pull request trigger for main. Capture the report start once in UTC and invoke the same calculation for both triggers. | GitHub Actions, Python report entry point | R-002, R-003, R-004 |
| D-002 | Reuse the existing Render evidence reader for authenticated requests, pagination, and UTC live timestamps. Select production arrivals by deploy ID using the start-exclusive, cutoff-inclusive window. Carry evidence gaps forward explicitly. | Render production service, `scripts/dora_evidence.py`, report evidence loader | R-001, R-004, R-007, R-008 |
| D-003 | Validate maintainer-confirmed attribution, join records to eligible arrivals by original Render deploy ID, and count distinct IDs whose intervention starts between live time and live time plus 24 hours, inclusive. | GitHub incident reader, change failure rate calculator | R-005, R-006 |
| D-004 | Compare pending incidents against eligible original deployments that have yet to be counted. Surface the issue reference if the available timing or missing timing leaves a possible addition to the count. Publish bounds, counts, percentage or unavailable status, and applicable evidence gaps in the workflow job summary. | Change failure rate calculator, report formatter, GitHub Actions job summary | R-001, R-004, R-007, R-008, R-009 |
| D-005 | Reconcile paginated Render production history on a schedule independently of report runs. Identify rollbacks from successful deploys with `trigger: rollback`. For other successful deploys, use Git ancestry and explicit promotion mappings to identify newly shipped original PRs labeled `production-hotfix`, whether merged directly into main or shipped through an unlabeled staging promotion. | Scheduled GitHub Actions workflow, Render production history, Git history, GitHub pull requests, promotion resolver | R-010, R-011 |
| D-006 | Key corrective entries by production service and corrective Render deploy ID. Serialize incident writes for the production service and look up a durable entry marker before writing. When creating an issue, include the marker and pending entry in the creation request so a retry can find the record after a lost response. Preserve existing maintainer attribution on repeat processing. | Incident writer workflow, GitHub issues | R-010, R-012 |

## Components and Flow

A report run captures its start time, computes the cutoff 24 hours earlier and the start 30 days before the cutoff, then reads Render arrivals and GitHub incident evidence. The calculator filters by live time and joins confirmed records to the original deployments. It considers intervention evidence through the original deployment's full 24-hour interval, including intervention starts after the reporting cutoff.

The formatter shows confirmed counts and a percentage when evidence is complete and the total is positive. A verified empty period yields two zeros and an unavailable rate. An evidence gap yields an unavailable rate with diagnostics and the confirmed-so-far label on any displayed counts.

The scheduled workflow scans successful production deploys in live-time order, including deploys that went live between scans and have since been deactivated. Resume from the last fully reconciled point after missed or partial runs. The report identifies scan or provenance gaps when they could affect the count. [Render deploy history](https://api-docs.render.com/reference/list-deploys) · [Render rollback API](https://api-docs.render.com/reference/rollback-deploy)

For hotfixes, adapt the ancestry and mapping approach from the existing promotion resolver. Compare original PRs reachable from the deployed revision with PRs already shipped to production. This detects hotfixes carried by later deploys when Render skips intermediate revisions and avoids recording the same hotfix again on a redeploy. When squash or rebase obscures ancestry, use a maintainer-reviewed mapping from the promotion revision to the original staging PR numbers. Flag missing or ambiguous provenance as incomplete evidence. [Existing promotion resolver](../../../scripts/dora_lead_time.py)

The writer checks for the corrective Render deploy ID before updating the explicitly linked issue or creating an issue. For a hotfix, read the issue link from the original PR. For a rollback, use the explicit issue linkage when available. Render the new issue body or linked issue comment from [the production incident template](../../templates/devops/production-incident.md). Populate it with the durable corrective deployment marker, intervention type, production live time, and corrective action links. Each entry marks attribution as pending until a maintainer confirms which original deployment caused the incident and records the intervention type and start time.

## Data and Interfaces

| Interface | Data |
| --- | --- |
| Report workflow | Manual dispatch or merged pull request into main, one UTC start timestamp, the existing `RENDER_API_KEY` secret, and the `DORA_RENDER_SERVICE_ID` and `DORA_RENDER_FIRST_DEPLOY_ID` variables |
| Render evidence | Production service, deployment ID, deployed revision, status, trigger, live time, and evidence completeness |
| Promotion evidence | Promotion revision and reviewed original staging PR numbers where Git ancestry obscures the original PRs |
| Corrective deployment | Corrective Render deploy ID, verified production-live outcome, intervention type, corrective action link, and explicit incident issue link when available |
| Incident record | Corrective deployment key and link, pending or maintainer-confirmed attribution, and for confirmed records the original Render deploy ID, causation confirmation, intervention type and start time |
| Report summary | Window start and cutoff in UTC, evidence status, available counts, rate or unavailable status, and missing evidence identifiers |

The reporting workflow reads deployment and issue evidence. The trusted incident writer has GitHub issue write access for recording corrective deployments.

## Evidence Outcomes

- S-028 through S-034 cover the report counts, both triggers, deduplication of original deployments, the inclusive 24-hour boundary, and the empty result.
- S-035, S-036, S-040, and S-041 cover missing history, identification of the specific pending incident, the reporting bounds, and publication when pending attribution cannot affect the count.
- S-037 through S-039 cover creation for rollback and direct hotfix, linked issue updates for a staging hotfix, and replay without duplicate entries.
