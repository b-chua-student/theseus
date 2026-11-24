# Brief: Track DORA deployment frequency

- ID: #157
- Owner: @b-chua-student
- Date: 2026-11-24
- Base SHA: `2bb7768f0ba278d5b4887e2d4c8f893e4c6d2218`

## Goal

Report production deployment counts so Theseus maintainers can see how often changes reach production.

## Users / Roles

- Theseus maintainers review deployment frequency.

## In Scope

- Identify the reporting period and report the count of deployments that reached production during that period.

## Non-Goals

- Changes to deployment operations.
- Reporting for other metrics.

## Constraints

- Count each deployment that reached production once.
- Exclude staging deployments and deployment attempts that never reach production.

## Known Touchpoints

- The Theseus DevOps requirements call for tracking deployment frequency.

## Assumptions

- No assumptions were recorded in the ticket.

## Open Questions

- What reporting period and cadence should be used? Deferred: The ticket leaves both choices open.
- How should rollbacks and redeployments be counted? Deferred: The ticket leaves their treatment open.

## Success Criteria

1. The report identifies the reporting period and counts each deployment that reached production during that period once.
2. Staging deployments and deployment attempts that never reach production contribute zero to the reported count.

## Reference Links

- [GitHub issue #157](https://github.com/b-chua-student/theseus/issues/157)
- [DORA metric definitions](https://dora.dev/guides/dora-metrics/)
