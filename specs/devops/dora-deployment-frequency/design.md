# Design — Track DORA deployment frequency

## Design

| ID | Decision | Components | Requirements |
| --- | --- | --- | --- |
| D-001 | Use the live timestamp from the designated production service as evidence that a deployment reached production. Apply the same check to every trigger type. | Render deployment history, deployment evidence reader | R-002, R-003 |
| D-002 | Sort qualifying events by their UTC timestamps and subtract the earlier timestamp from the later one for each adjacent pair. | Deployment frequency calculator | R-001, R-003 |
| D-003 | Use a GitHub Actions job summary to display each calculated interval or an explicit unavailable message when the verified input contains fewer than two qualifying events. | Reporting workflow, report formatter | R-001, R-004 |

## Components and Flow

The reporting workflow reads deployment history for the designated production service. Reuse the deployment lead-time script's Render pagination and timestamp handling where applicable. The evidence reader supplies the production arrival events to the calculator, which sorts them chronologically and passes the adjacent-pair durations to the formatter. A retrieval failure surfaces as a reporting error so the unavailable message describes a verified count of zero or one.

## Data and Interfaces

The evidence reader needs the production service identity, deployment identity, evidence of reaching production, and the corresponding timestamp. Retain one event per deployment identity. The report consumes a chronological list of elapsed durations or an unavailable result. The cadence, history window, and eligibility of rollback and redeployment events remain open in [requirements.md](requirements.md#open-questions).

The workflow uses the `RENDER_API_KEY` GitHub Actions secret to authenticate Render API requests and the `DORA_RENDER_SERVICE_ID` repository variable to identify the production service. `DORA_RENDER_FIRST_DEPLOY_ID` anchors verification of the service's deployment history. Verify the first deployment independently against that history, including failed attempts. Accept `empty` only for a verified never-deployed service and replace it with the first deployment ID when one exists. The calculator still applies D-001 to every event, including the first attempt.

`DORA_FEATURE_LABEL` identifies feature PRs, including historical PRs. Deployment frequency uses service deployment events and requires no PR label input. See [repo-findings.md](repo-findings.md) for the configuration definitions.

## Evidence Outcomes

- S-023 yields two intervals of 2 and 3 hours.
- S-024 yields a single 4-hour interval despite intervening staging and unsuccessful attempts.
- S-021 yields one 6-hour interval between automatic and manual production deployments despite an intervening manual attempt that never reached production.
- Both examples of S-022 yield the unavailable message.
