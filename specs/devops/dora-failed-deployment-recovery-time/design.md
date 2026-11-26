# Design — Track failed deployment recovery time

## Design

| ID | Decision | Components | Requirements |
| --- | --- | --- | --- |
| D-001 | Use the GitHub production incident issue as the incident record. Key the report by issue number. Let maintainers open an issue before reconciliation or add recovery details to an issue already created by change failure rate (CFR) reconciliation. Link all corrections for the incident to that issue. | Production incident issue template, GitHub issues, incident reader | R-004, R-005, R-006, R-014 |
| D-002 | Discover issues with the `dora-recovery-incident` label across all issue states. Provision the label during rollout and check that it exists before discovery. Require maintainer-confirmed eligibility before including an issue in entries or aggregates. | Incident reader, recovery calculator | R-001 |
| D-003 | Read the confirmed degradation and restoration times and their evidence from the incident. Use a linked corrective deployment's Render Live time when it coincides with confirmed recovery. Calculate elapsed time between the two confirmed instants for restored incidents with both times. | Incident reader, incident timeline, Render evidence, recovery calculator | R-002, R-003, R-004 |
| D-004 | Classify each qualifying issue by restoration status first and timestamp completeness second. Build the median and sample count from completed durations. Render the incident entries, all three counts, and the required message when there are zero durations. | Recovery calculator, recovery report formatter | R-005, R-006, R-007, R-008, R-009 |
| D-005 | Keep recovery-specific parsing, calculation, and formatting in a dedicated reporting entry point. Reuse the existing GitHub issue access and maintainer permission check, and keep the shared incident fields compatible with the current change failure rate reader and writer. Initialize GitHub access independently of the change failure rate configuration. | Recovery reporting entry point, GitHub issue access in `scripts/dora_change_failure_rate.py`, production incident issue template | R-010 |
| D-006 | Publish the recovery report in the job summary of a dedicated GitHub Actions workflow with manual dispatch. Capture the run start once in UTC and read current incident records on each run, covering all qualifying recorded incidents. | GitHub Actions, recovery reporting entry point, incident reader, job summary | R-011 |
| D-007 | Read maintainer-authored timeline comments in creation order, with comment ID as the tie-breaker. Use the latest valid explicit resolution of each timestamp conflict. Treat any outstanding disputed time as unknown and treat restoration before degradation as an unknown restoration time. Preserve restoration status and include an issue-linked diagnostic for the evidence problem on a restored incident. | Incident reader, timeline validation, recovery calculator, report formatter | R-005, R-008, R-012 |
| D-008 | Preserve incident loading failures as a distinct result and display incomplete evidence in the job summary. Use the empty report only after a successful load confirms there are zero qualifying incidents. | Incident reader, reporting entry point, job summary | R-009, R-013 |

## Components and Flow

A maintainer opens a production incident issue when the failure can be recorded. If CFR reconciliation already opened an issue for that incident, the maintainer adds the recovery label and confirmation to the existing issue. The CFR marker and the corrective deployment's Live time alone do not establish eligibility. When service returns, the maintainer posts the updated restoration status on the same issue, even if the time is unknown.

Link each corrective hotfix using `Incident: #123` in the original PR body and apply the existing `production-hotfix` label. Link each rollback using `DORA rollback: <deploy-id>` on its own line in the issue body or a maintainer comment. When a recovery issue exists first, add these links before reconciliation processes the correction so the CFR writer can reuse it. Preserve existing CFR markers and attribution comments.

If a correction was recorded under a separate CFR issue before it was linked, use that CFR issue as the canonical recovery record. Repost the qualifying confirmation and restoration status, then repost the timeline claims in their original order, preserving explicit resolutions, on the canonical issue and link the duplicate issue to it. Where several CFR issues already contain correction records, keep the CFR records in place and choose one issue as the canonical recovery record. Document the other corrections on that issue using links to their existing CFR entries. Apply the recovery label only to the canonical issue and remove it from any duplicate. Verify that the next report counts one incident and that existing CFR evidence remains available.

A maintainer runs the dedicated workflow from the Actions tab. The job captures its start time in UTC, reads current incident records, and publishes the report in the job summary.

If incident records cannot be loaded, the report publishes an incomplete-evidence result. After a successful load, it reads each incident once, checks eligibility, and validates the confirmed timeline before classifying the incident. For a qualifying issue, an unrestored service produces an “Unresolved” entry. A restored service with an incomplete timeline produces a “Missing timestamp” entry. A restored service with both times produces an elapsed duration. The report sorts completed durations for the median and averages the two middle values when the sample count is even.

## Data and Interfaces

| Interface | Data |
| --- | --- |
| Production incident issue | Issue number, `dora-recovery-incident` label, eligibility and restoration confirmations, timeline comments, and optional corrective deployment links |
| Recovery confirmation comment | A `DORA recovery:` line containing a JSON object with `environment` (string), `degraded`, `deploymentCaused`, `immediateIntervention`, and `restored` (booleans) |
| Timeline evidence comment | A `DORA recovery timeline:` line containing a JSON object with `field` (`degradation` or `restoration`), `timestamp` (ISO 8601 with UTC offset), `source` (`monitoring` or `maintainer-timeline`), `evidence` (nonempty reference or description), and `resolvesConflict` (boolean). A restoration comment citing recovery at Render Live also includes `correctiveDeployId` (the linked Render deploy ID). See the validation and example below. |
| Corrective deployment evidence | Optional links to corrective actions and their Render Live times, with confirmation when normal service returned at a linked Live time |
| Recovery report | UTC run time, one entry per qualifying issue, duration or blank duration with the applicable status, completed recovery count, unresolved count, missing-timestamp count, and median or empty-sample message, and issue-linked timeline diagnostics where applicable. If incident records cannot be loaded, publish an incomplete-evidence result. |

Reuse the existing GitHub maintainer permission check for both comment types. Use the latest valid recovery confirmation by comment creation time, then comment ID. An issue qualifies when `environment` is `production` and `degraded`, `deploymentCaused`, and `immediateIntervention` are all true. Read `restored` independently of the timeline comments. Include examples of both comment formats in the production incident template so maintainers can add them to new or CFR-generated issues.

Process timeline comments independently for each field. Compare normalized instants so equivalent UTC offsets agree. A distinct ordinary claim makes the time disputed. A valid comment with `resolvesConflict` set to true establishes the confirmed time and supersedes earlier claims for that field. A later conflicting ordinary claim reopens the dispute. Malformed comments and comments from authors without maintainer permission do not supply a timestamp or resolve a dispute. After resolving each field, validate degradation and restoration order before calculating a duration.

The [repository configuration inventory](repo-findings.md) lists settings used by existing metric workflows. The recovery workflow uses the repository identifier and workflow token for GitHub issue and comment access. It reads confirmed Render Live timestamps from incident timeline evidence, so `RENDER_API_KEY`, `DORA_RENDER_SERVICE_ID`, and `DORA_RENDER_FIRST_DEPLOY_ID` are unnecessary for a recovery run. Issue discovery uses `dora-recovery-incident`. The feature PR selector `DORA_FEATURE_LABEL` applies to other reporting.

Check that the discovery label exists using the repository label endpoint before listing issues. A missing label or a failed check produces the incomplete-evidence result. A successful lookup followed by a successful list with no qualifying issues produces the empty report.

When `correctiveDeployId` is present, accept it only on a restoration claim and require a matching deployment ID in a CFR correction marker on the issue or in a maintainer-authored `DORA corrective deploy: <deploy-id>` line on the issue. Use the explicit line when a correction has an existing CFR record elsewhere or has yet to be reconciled. The `timestamp` is the maintainer-confirmed Live instant. Maintainers use this field only when the cited evidence confirms that normal service returned at that instant. The report validates the structured fields, link, and presence of the evidence text. Maintainers verify the evidence itself. This report reads the incident evidence without a Render API lookup. An invalid Live claim supplies no timestamp and cannot resolve a dispute.

```text
DORA corrective deploy: dep-example123
DORA recovery timeline: {"field":"restoration","timestamp":"2026-11-24T10:45:00Z","source":"monitoring","evidence":"The linked Render deploy went Live at 10:45 UTC. Production monitoring confirms normal service returned at that instant.","resolvesConflict":false,"correctiveDeployId":"dep-example123"}
```

## Evidence Outcomes

- S-049, S-050, S-054, and S-055 exercise the confirmed recovery time with a later restoration, a matching Live time, a recovery without a corrective deployment, and a maintainer linking multiple hotfixes to one existing incident.
- S-048 and S-051 exercise exclusion from entries and aggregates for a healthy production service after a failed deployment attempt and for each disqualifying condition.
- S-052, S-053, and S-058 exercise reporting an unresolved incident before a correction, recording it through the maintainer entry point, and classifying restored incidents with each combination of missing timestamps.
- S-046, S-047, S-056, and S-057 exercise mixed statuses, zero completed samples with qualifying incidents, zero qualifying incidents, and an even sample count.
- S-059 verifies that manual refresh includes older and newly recorded qualifying incidents and displays the run time in UTC.
- S-060 and S-061 verify disputed degradation or restoration timestamps, out-of-order timestamps, and recovery from a conflict through explicit maintainer confirmation.
- S-062 verifies that an incident load failure produces an incomplete-evidence result. Exercise a failed label lookup separately from a successful load with no qualifying incidents.

- The compatibility check for D-001 and D-005 verifies that a CFR-generated issue is excluded before recovery confirmation and that adding recovery details to that issue yields one qualifying entry. It also verifies that linking corrections to an existing recovery issue preserves the existing CFR recording and reporting behavior.

- Verify the late-link procedure leaves one qualifying recovery issue while preserving existing CFR correction and attribution evidence. Verify a valid linked Live claim supplies a restoration timestamp and an unlinked corrective deploy ID cannot supply one.
