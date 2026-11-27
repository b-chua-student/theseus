# Design — Feature PR merge-to-production lead time

## Design

| ID | Decision | Components | Requirements |
| --- | --- | --- | --- |
| D-001 | Classify feature PRs using the repository-configured label. Resolve original feature PR identity and merge time using GitHub metadata, revision ancestry, and maintainer-reviewed evidence for obscured promotions. | GitHub, provenance resolver | R-002 |
| D-002 | Validate production history, deduplicate by earliest live timestamp, and calculate metrics within a half-open UTC window. | Render history reader, report calculator | R-001, R-003 |
| D-003 | Use a report-only workflow triggered solely by manual dispatch. Production deploys start through a maintainer’s manual action. | GitHub Actions, Render production service | R-001, R-005, R-006 |
| D-004 | Publish metrics after evidence validation and sanitize errors and logs. | Workflow, evidence readers, report renderer | R-004 |

## Components and Flow

A maintainer initiates a production deployment manually. Manually triggered report runs retrieve historical deployment records through read-only operations.

## Data and Interfaces

| Input | Data used |
| --- | --- |
| GitHub Actions repository variable `DORA_FEATURE_LABEL` | Feature PR label for current and historical PRs. Configure it as `enhancement` for Theseus. |
| GitHub PR metadata | Stable PR identity, base branch, original UTC merge timestamp, and labels matched against the configured feature PR label |
| Git history and promotion evidence | Deployed revision ancestry and the set of original PRs carried by each promotion, including where squash or rebase rewrites SHAs |
| Render deployment history | Designated production service ID, deployment ID, deployed SHA, successful live outcome, and UTC live timestamp |

Before implementation, confirm the production service, API evidence and retention, feature classification, allowed merge strategies, and the available promotion records. For history-preserving merges, use commit reachability from the deployed SHA and PR metadata. For rewritten history, use maintainer-reviewed promotion or merge evidence tying the production revision to the original PRs. A branch name, PR title, or current branch tip alone cannot establish what a historical deployment carried.

Fetch all relevant pages and enough earlier history to establish each candidate PR's first live deployment. An explicitly verified starting point or a verified record of first deployments can support that proof. If pagination, missing revisions, ambiguous provenance, or retention gaps prevent proof, fail the run. A service with complete evidence and zero qualifying PRs produces a valid empty report.

## Evidence Outcomes

1. Capture a single UTC run timestamp as the window end and subtract 30 days for the start. Use the half-open interval `[start, end)`.
2. For each successful live deployment on the designated service before the window end, resolve the feature PR identities proven present in the deployed revision. Use each feature PR's original merge timestamp.
3. For each PR, keep the earliest qualifying live timestamp. Reject inconsistent evidence such as a live timestamp before the PR merged.
4. Keep PRs whose first live timestamps fall inside the window. Compute elapsed hours per PR and take the median, averaging the two middle samples when the count is even. Round only when formatting for display. Show the median as unavailable when the count is zero.

## GitHub Actions

Proposed implementation is a repository-local reporting script called by a dedicated workflow. Separate evidence retrieval and provenance resolution from calculation and rendering so the calculation and failure paths can be tested with fixtures.

Use manual dispatch and a GitHub Actions job summary as the on-demand report surface. The report uses read-only Render history operations.

Grant the workflow read access to the necessary GitHub data and pass the Render API credential through an Actions secret. Pass `vars.DORA_FEATURE_LABEL` to the script as `DORA_FEATURE_LABEL`. If the label setting is missing or blank, emit a sanitized configuration diagnostic and withhold the count and median. On failure, emit a concise diagnostic describing the evidence gap or retrieval failure. Keep authorization headers, raw API responses, and secret values out of logs. Write the report only after validation and calculation succeed.
