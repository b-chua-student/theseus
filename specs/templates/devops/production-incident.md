{marker}
Production {kind} went live at {live}.

{links}

Original deployment attribution is pending maintainer confirmation.

Use the [incident attribution instructions](https://github.com/{repo}/blob/main/specs/devops/dora-change-failure-rate/operations.md#confirm-attribution) to update this record.

## Failed deployment recovery

During rollout, create the repository label with:

```sh
gh label create dora-recovery-incident --color B60205
```

Add the `dora-recovery-incident` label to this issue. If reconciliation already
opened an issue for the incident, add the label and recovery comments there.
Use one issue for the incident and all its corrective deployments.

A maintainer posts a comment with one line like the following after confirming
production degradation, deployment causation, and the need for immediate
intervention.

```text
DORA recovery: {{"environment":"production","degraded":true,"deploymentCaused":true,"immediateIntervention":true,"restored":false}}
```

When normal service returns, post a new comment with the same fields and
`"restored":true`, even if the restoration time is unknown or service recovered
without a corrective deployment.

Post a separate timeline comment for each known time. Use an ISO 8601 timestamp
with a UTC offset and cite production monitoring or a maintainer-confirmed
timeline. Leave unknown times unrecorded.

```text
DORA recovery timeline: {{"field":"degradation","timestamp":"2026-11-24T10:00:00Z","source":"monitoring","evidence":"Production error-rate alert","resolvesConflict":false}}
DORA recovery timeline: {{"field":"restoration","timestamp":"2026-11-24T10:45:00Z","source":"maintainer-timeline","evidence":"Verified normal service at 10:45 UTC","resolvesConflict":false}}
```

If evidence disagrees about a time, post a new timeline comment for that field
with the confirmed timestamp and `"resolvesConflict":true`. Use a linked
corrective deployment's Render Live time only when the evidence confirms normal
service returned at that instant.

If CFR already recorded the correction on a separate issue, keep that issue
and its CFR evidence. On the original incident, add a maintainer comment with
`DORA corrective deploy: dep-example123` on its own line and link to the
separate issue. Repeat for each correction. Keep the recovery label,
confirmation, and timeline on the original incident. If the separate issue
also has the recovery label for the same incident, remove that label there.

To use a linked Render Live time, post a restoration timeline comment with
the corrective deployment ID and evidence that normal service returned at
that instant.

```text
DORA corrective deploy: dep-example123
DORA recovery timeline: {{"field":"restoration","timestamp":"2026-11-24T10:45:00Z","source":"monitoring","evidence":"Render went Live and monitoring confirmed normal service at 10:45 UTC","resolvesConflict":false,"correctiveDeployId":"dep-example123"}}
```

Run **DORA failed deployment recovery time** from the Actions tab to read
the current incident records in the job summary.
