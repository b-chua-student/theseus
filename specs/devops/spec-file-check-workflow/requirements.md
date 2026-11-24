# Requirements — Check spec files against repository templates

- Ticket: `tickets/spec-file-checking.md`

## Requirements

| ID | Requirement | Source | Ticket lines | Scenarios |
| --- | --- | --- | --- | --- |
| R-001 | Run the spec check when a pull request adds or changes a requirements, design, or tasks file in a feature directory. A change limited to templates, tickets, or Gherkin does not trigger the check. | from ticket | 13, 40 | S-012, S-014 |
| R-002 | Limit validation to affected feature directories so errors in unrelated legacy specs do not fail the check. | from ticket | 32 | S-013 |
| R-003 | Pass conforming spec files. Fail when a spec file lacks a required heading or table column, or contains a malformed or duplicate requirement, design, or task ID within its table. Apply the corresponding repository templates and their traceability conventions. | from ticket | 13, 18, 19, 27 | S-012, S-015 |
| R-004 | Fail when a requirement lacks its source ticket reference, cites a nonexistent or blank line in that ticket, or references a scenario absent from the feature's Gherkin. | from ticket | 14, 20, 27 | S-016 |
| R-005 | Fail for invalid design or task references, a requirement without a design decision, a design decision without a task, or a scenario without a verification task. | from ticket | 14, 21, 27 | S-017 |
| R-006 | Fail when the task graph disagrees with the table, task dependencies contain a cycle, an independent task is outside wave 1, or a dependent task's wave is not one after its latest prerequisite. | from ticket | 22, 27 | S-018 |
| R-007 | Identify the affected file and failed rule for each failure. | from ticket | 23 | S-015, S-016, S-017, S-018 |
| R-008 | Keep the existing intake and Gherkin checks available during pull request review. | from ticket | 28 | S-012 |

## Open Questions

- None. The intake records the resolution of the trigger question on ticket line 40.
