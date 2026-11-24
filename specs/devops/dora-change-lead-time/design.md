# Design — Feature PR merge-to-production lead time

## Inputs and provenance

| Input | Data used |
| --- | --- |
| GitHub PR metadata | Stable PR identity, base branch, original UTC merge timestamp, and the maintainer-approved feature classification signal |
| Git history and promotion evidence | Deployed revision ancestry and the set of original PRs carried by each promotion, including where squash or rebase rewrites SHAs |
| Render deployment history | Designated production service ID, deployment ID, deployed SHA, successful live outcome, and UTC live timestamp |

Before implementation, confirm the production service, API evidence and retention, feature classification, allowed merge strategies, and the available promotion records. For history-preserving merges, use commit reachability from the deployed SHA and PR metadata. For rewritten history, use verifiable promotion or merge evidence tying the production revision to the original PRs. A branch name, PR title, or current branch tip alone cannot establish what a historical deployment carried.

Fetch all relevant pages and enough earlier history to establish each candidate PR's first live deployment. An explicitly verified starting point or a verified record of first deployments can support that proof. If pagination, missing revisions, ambiguous provenance, or retention gaps prevent proof, fail the run. A service with complete evidence and zero qualifying PRs produces a valid empty report.

## Calculation

1. Capture a single UTC run timestamp as the window end and subtract 30 days for the start. Use the half-open interval `[start, end)`.
2. For each successful live deployment on the designated service before the window end, resolve the feature PR identities proven present in the deployed revision. Use each feature PR's original merge timestamp.
3. For each PR, keep the earliest qualifying live timestamp. Reject inconsistent evidence such as a live timestamp before the PR merged.
4. Keep PRs whose first live timestamps fall inside the window. Compute elapsed hours per PR and take the median, averaging the two middle samples when the count is even. Round only when formatting for display. Show the median as unavailable when the count is zero.

## GitHub Actions

Proposed implementation is a repository-local reporting script called by a dedicated workflow. Separate evidence retrieval and provenance resolution from calculation and rendering so the calculation and failure paths can be tested with fixtures.

Use manual dispatch and a GitHub Actions job summary as the on-demand report surface. Use the same job summary for scheduled publication, with the weekly UTC schedule confirmed by maintainers. Gate the scheduled path with a repository variable that defaults to disabled, and enable it only after a maintainer verifies the manual run.

Grant the workflow read access to the necessary GitHub data and pass the Render API credential through an Actions secret. On failure, emit a concise diagnostic describing the evidence gap or retrieval failure. Keep authorization headers, raw API responses, and secret values out of logs. Write the report only after validation and calculation succeed.
