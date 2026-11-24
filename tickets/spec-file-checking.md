# [spec-file-checking] As a contributor, I can check spec files against the repository templates

## Intent

Catch structural and traceability errors in spec files during pull request review.

## Context

Pull requests already get checks for intake briefs and Gherkin. The requirements, design, and tasks templates define the structure and references expected in the next workflow stage.

## Scope

- Check new or changed `requirements.md`, `design.md`, and `tasks.md` in feature directories against the corresponding templates.
- Validate references among a feature's spec files, source ticket, and Gherkin scenarios.

## Expected Outcomes

- [ ] A pull request with conforming spec files passes the spec check.
- [ ] The check fails when a spec file lacks a required heading or table column, or contains a malformed or duplicate requirement, design, or task ID within its table.
- [ ] The check fails when a requirement lacks its source ticket reference, cites a nonexistent or blank ticket line, or references an unknown scenario.
- [ ] The check fails when design or task references are invalid, a requirement has no design decision, a design decision has no task, or a scenario has no verification task.
- [ ] The check fails when the task graph and table disagree, dependencies contain a cycle, or task waves do not match the prerequisites.
- [ ] Each failure identifies the affected file and the rule that failed.

## Rules / Constraints

- Use the corresponding repository spec templates for required headings, columns, and traceability conventions.
- Keep the existing intake and Gherkin checks available.

## Non-Functional Requirements

- Check the affected feature directories so unrelated legacy specs do not cause failures.

## Out of Scope

- Automatically rewriting spec files or judging the quality of their prose.

## Open Questions

- Should a pull request that changes only a template, ticket, or Gherkin file also trigger spec validation?

## Security Acceptance Criteria

- [ ] The spec check rejects option-like values in either revision argument and reports which input is invalid.
- [ ] Valid revision inputs continue to select changes for the spec check, with or without a head revision.

## Output Paths

Each feature lives in `specs/<context>/<feature_name>/`.

- Intake brief: `brief.md`
- Gherkin: `gherkin.feature`
- Spec files: `requirements.md`, `design.md`, and `tasks.md`

## Definition of Done

- [ ] Intake generated and approved
- [ ] Gherkin generated and approved
- [ ] Open questions resolved
- [ ] Spec, Gherkin, and code in sync
- [ ] Reviewed and merged
