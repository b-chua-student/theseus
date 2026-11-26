---
name: Production incident
about: Record a deployment-caused production incident for DORA reporting.
title: "[Production incident] "
---

## Incident summary

<!-- Describe what happened in production and the observed impact. -->

## Failed deployment recovery

Add the `dora-recovery-incident` label to this issue. If reconciliation already
opened an issue for the incident, add the label and recovery comments there.
Use one issue for the incident and all its corrective deployments.

A maintainer posts a comment with one line like the following after confirming
production degradation, deployment causation, and the need for immediate
intervention.

```text
DORA recovery: {"environment":"production","degraded":true,"deploymentCaused":true,"immediateIntervention":true,"restored":false}
```

When normal service returns, post a new comment with the same fields and
`"restored":true`, even if the restoration time is unknown or service recovered
without a corrective deployment.

Post a separate timeline comment for each known time. Use an ISO 8601 timestamp
with a UTC offset and cite production monitoring or a maintainer-confirmed
timeline. Leave unknown times unrecorded.

```text
DORA recovery timeline: {"field":"degradation","timestamp":"2026-11-24T10:00:00Z","source":"monitoring","evidence":"Production error-rate alert","resolvesConflict":false}
DORA recovery timeline: {"field":"restoration","timestamp":"2026-11-24T10:45:00Z","source":"maintainer-timeline","evidence":"Verified normal service at 10:45 UTC","resolvesConflict":false}
```

If evidence disagrees about a time, post a new timeline comment for that field
with the confirmed timestamp and `"resolvesConflict":true`. Use a linked
corrective deployment's Render Live time only when the evidence confirms normal
service returned at that instant.

## Corrective action

- Intervention type (rollback or hotfix, if applicable):
- Intervention start time (include the UTC offset):
- Link to the Render rollback deployment or original hotfix pull request:

<!--
To link this issue to a hotfix, add `Incident: #123` to the original
hotfix PR body, replacing 123 with this issue number. Apply the
`production-hotfix` label to that PR.

To link a rollback, a maintainer adds `DORA rollback: dep-EXAMPLE` on
its own line in this issue body or a comment. Replace dep-EXAMPLE with
the corrective Render deploy ID.

Add links to this issue before reconciliation processes each correction.
-->

## Original deployment attribution

- Status: Pending maintainer confirmation
- Original Render production deploy ID (if known):
- Did the original deployment cause the incident (yes, no, or unknown):

A maintainer can confirm the original deployment and its role here as soon as
the evidence is available.

After reconciliation records the corrective deployment, a maintainer
records the original deploy ID, whether it caused the incident, the
intervention type and start time, and the corrective action link in a
`DORA attribution:` comment. See the
[attribution instructions](https://github.com/b-chua-student/theseus/blob/main/specs/devops/dora-change-failure-rate/operations.md#confirm-attribution).
