# Design — Track deployment rework rate

## Design

| ID | Decision | Components | Requirements |
| --- | --- | --- | --- |
| D-001 | Add a dedicated manual GitHub Actions workflow with read-only access and capture one UTC report start for the run. | Deployment rework workflow, report entry point | R-001, R-002 |
| D-002 | Reuse the Render evidence reader for the configured production service. Key verified arrivals by production deploy ID and select those with live times in the half-open UTC window. Retain the history verification outcome alongside the arrivals. | Render evidence reader, deployment window selector | R-002, R-003, R-007, R-008 |
| D-003 | Reuse the existing GitHub reader and maintainer checks to read production incident issues and comments. Collect incident threads independently so a failed read can be recorded alongside valid evidence from other threads. Match explicit rework confirmation to the production service and corrective deploy ID. Associate hotfix or rollback candidates with that same identity when supported by evidence. Read explicit maintainer dispositions for deployments with no qualifying rework and match them by production service and deploy ID. Classify each verified deployment once as confirmed rework, reviewed with no qualifying rework, or awaiting review. Carry forward gaps in incident evidence and use their deployment scope to determine which classifications remain open. | GitHub incident reader, rework evidence reader, deployment classifier | R-004, R-005, R-008, R-009, R-011 |
| D-004 | Build the report from the verified production population and classification evidence. Publish the counts and percentage, the verified empty result, or the incomplete-evidence result to the job summary. | Rate calculator, job summary formatter | R-003, R-005, R-006, R-007, R-008 |
| D-005 | Add a **Deployment rework** section to the existing production incident template. Show maintainers how to confirm each qualifying corrective deployment in an incident comment. Use the same comment format as the rework evidence reader. | Production incident template, rework evidence reader | R-004, R-010 |

## Components and Flow

1. The workflow captures its start in UTC and passes it to the report. The report uses the interval from 30 days before that start through, but excluding, the start itself.
2. The Render reader checks production history against the configured first-deployment anchor, including relevant pagination and historically live deployments that were later deactivated. If a gap could change the production count, the report marks the total unverified and withholds the percentage. A verified empty population takes the empty reporting path immediately.
3. For a nonempty verified population, the incident reader reads issue records and comments. The classifier joins valid confirmations to in-window production arrivals and counts unique corrective deploy IDs. For each remaining arrival, the classifier checks for an explicit maintainer disposition of no qualifying rework. Arrivals with neither valid disposition await review, even without incident links or candidate flags. For each incident evidence gap, identify verified arrivals whose classification could change. Use known affected deployment IDs where supported by the available evidence. If the affected IDs are unknown, consider the entire verified population and include every arrival whose classification could still change. Move those arrivals to awaiting review, including any with a no-rework disposition, and preserve confirmed rework where the gap cannot change the confirmation. Count awaiting review by distinct deploy ID across gaps and missing dispositions. Any arrival awaiting review produces the incomplete-evidence result.
4. The formatter publishes the applicable result in the job summary. The workflow uses read access to Render and GitHub and performs no deployment or incident reconciliation operations.

## Data and Interfaces

- The workflow uses `RENDER_API_KEY`, `DORA_RENDER_SERVICE_ID`, and `DORA_RENDER_FIRST_DEPLOY_ID`. The anchor identifies the earliest deployment attempt, including failed attempts. The value `empty` denotes a verified never-deployed service.
- A production arrival carries the configured service ID, deploy ID, and verified UTC live time. History verification carries whether available evidence establishes the in-window population.
- Rework evidence identifies the incident, production service, corrective deploy ID, and whether an authorized maintainer explicitly confirmed the deployment was an unplanned response. Existing correction markers can identify candidates. The change failure attribution parser requires a causal deploy and intervention timing and can reject confirmations across multiple issues. Read rework evidence independently of those rules and preserve existing attribution and correction markers.
- Incident evidence collection returns validated confirmations and evidence gaps. Each gap carries the affected production deploy IDs when known or an unknown-scope flag. Preserve evidence from successfully read incident records when another incident record or comment could not be read.
- On a production incident issue, a maintainer posts `/dora rework <service-id> <deploy-id>` on its own line in a comment, using the corrective deployment ID. The template explains when to post the command and to record each qualifying deployment separately.
- In the repository issue identified by `DORA_DEPLOYMENT_REVIEW_ISSUE`, a maintainer posts `/dora no-rework <service-id> <deploy-id>` on its own line in a comment. Both commands use the existing maintainer authorization check and exact service and deploy ID matching.
- The job summary carries the reporting window, verified counts where available, and either the computed rate or the applicable evidence status.

Design references include the [repository findings](repo-findings.md), [pipeline documentation](../../../docs/PIPELINE.md), and [DORA metric context](../dora-context.md).

## Evidence Outcomes

- Four verified arrivals with two confirmed corrective deployments produce 2 rework deployments, 4 production deployments, and 50%. Repeated confirmations for one corrective deployment contribute one count.
- A verified arrival exactly at the window start qualifies even when its incident began earlier. Arrivals at and after the report start are excluded.
- A verified empty period displays zero for both counts and **N/A — no production deployments**. A verified nonempty period with zero qualifying deployments displays **0%**.
- If incomplete incident evidence could change the numerator, the report shows the verified production total, confirmed rework count, number awaiting review, and **Incomplete evidence**. If incomplete production history could change the denominator, the report marks the production total unverified and shows **Incomplete evidence**. Both outcomes omit the rate.
- With one confirmed rework deployment and two recorded no-rework deployments, a gap that could change one no-rework classification yields 3 verified deployments, 1 confirmed rework deployment, and 1 awaiting review. If affected IDs are unknown and a fourth deployment already lacks a disposition, all three potentially affected deployments await review. The confirmed rework count stays at 1 and both reports omit the percentage.
- The production incident template displays **Deployment rework** guidance for recording a specific deployment that went live in production as an unplanned response to the incident.
