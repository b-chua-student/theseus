---
name: Production incident
about: Record a production rollback or hotfix for DORA change failure rate.
title: "[Production incident] "
---

## Incident summary

<!-- Describe what happened in production and the observed impact. -->

## Corrective action

- Intervention type (rollback or hotfix):
- Intervention start time (include the UTC offset):
- Link to the Render rollback deployment or original hotfix pull request:

<!--
To link this issue to a hotfix, add `Incident: #123` to the original
hotfix PR body, replacing 123 with this issue number. Apply the
`production-hotfix` label to that PR.

To link a rollback, a maintainer adds `DORA rollback: dep-EXAMPLE` on
its own line in this issue body or a comment. Replace dep-EXAMPLE with
the corrective Render deploy ID.
-->

## Original deployment attribution

- Status: Pending maintainer confirmation
- Original Render production deploy ID (if known):

After reconciliation records the corrective deployment, a maintainer
records the original deploy ID, whether it caused the incident, the
intervention type and start time, and the corrective action link in a
`DORA attribution:` comment. See the
[attribution instructions](https://github.com/b-chua-student/theseus/blob/main/specs/devops/dora-change-failure-rate/operations.md#confirm-attribution).
