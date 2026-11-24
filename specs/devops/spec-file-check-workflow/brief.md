# Brief: Check spec files against repository templates

- ID: #163
- Owner: b-chua-student
- Date: 2026-11-24
- Base SHA: 2a47c0eef9c3b2e49d8a902c2a6ce80d92b1dacd

## Goal

Catch structural and traceability errors in spec files during pull request review.

## Users / Roles

- Contributors submitting pull requests that change spec files.

## In Scope

- Check new or changed `requirements.md`, `design.md`, and `tasks.md` in feature directories.
- Validate references among each affected feature's spec files, source ticket, and Gherkin scenarios.
- Validate the revision inputs used to select changes.

## Non-Goals

- Automatically rewriting spec files or judging the quality of their prose.

## Constraints

- Use the corresponding repository templates for required headings, table columns, and traceability conventions.
- Limit validation to affected feature directories and keep the existing intake and Gherkin checks available.

## Known Touchpoints

- Existing pull request checks for intake briefs and Gherkin.
- Repository requirements, design, and tasks templates.

## Assumptions

- None recorded.

## Open Questions

- Should template-only, ticket-only, or Gherkin-only changes trigger spec validation? Resolved in the issue. A spec file change is required to trigger the check.

## Success Criteria

1. A pull request with conforming spec files passes the spec check.
2. The check fails for a missing required heading or table column, or a malformed or duplicate requirement, design, or task ID within its table.
3. The check fails when a requirement lacks its source ticket reference, cites a nonexistent or blank ticket line, or references an unknown scenario.
4. The check fails for invalid design or task references, a requirement without a design decision, a design decision without a task, or a scenario without a verification task.
5. The check fails when the task graph and table disagree, dependencies form a cycle, or task waves do not match their prerequisites.
6. Each failure identifies the affected file and the rule that failed.
7. Unrelated legacy specs do not cause a pull request to fail the spec check.
8. A pull request that changes only a template, ticket, or Gherkin file does not trigger the spec check.
9. The existing intake and Gherkin checks remain available during pull request review.
10. The spec check rejects an option-like value in either revision argument and identifies the invalid input.
11. Valid revision inputs select changes for the spec check, with or without a head revision.

## Reference Links

- [GitHub issue #163](https://github.com/b-chua-student/theseus/issues/163)
