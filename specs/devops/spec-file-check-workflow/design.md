# Design — Check spec files against repository templates

## Design

| ID | Decision | Components | Requirements |
| --- | --- | --- | --- |
| D-001 | Use a dedicated pull request workflow that selects added or modified spec files and deduplicates their parent feature directories. The existing intake and Gherkin workflow continues to run on its own triggers. | Spec check workflow, pull request change list, intake and Gherkin workflow | R-001, R-002, R-008 |
| D-002 | Read required headings and table columns from the corresponding templates. Parse the feature tables and validate the ID format and uniqueness within each table. | Repository spec templates, Markdown parser, structure validator | R-003 |
| D-003 | Resolve the requirements file's ticket entry and check each cited line against the ticket's original one-based line numbers. Match scenario references against the feature's Gherkin tags. | Requirements validator, source ticket, Gherkin scenario tags | R-004 |
| D-004 | Resolve design and task references against the feature's parsed IDs and check coverage from requirements to design decisions, from design decisions to tasks, and from scenarios to verification tasks. | Traceability validator, requirements table, design table, task table, Gherkin scenario tags | R-005 |
| D-005 | Compare the Mermaid node and edge sets with the task table, including standalone nodes and prerequisite-to-dependent edge direction. Check for cycles before computing expected waves from prerequisites. | Dependency validator, task table, Mermaid dependency graph | R-006 |
| D-006 | Report each validation failure with the affected repository-relative path and failed rule. Return a failing check status if any validation rule fails. | Spec validator, workflow diagnostics, pull request check status | R-003, R-007 |

## Components and Flow

The pull request workflow filters the change list for added or modified requirements, design, and tasks files under `specs/<context>/<feature>/`. It passes the distinct parent directories to the validator. Changes confined to templates, source tickets, or Gherkin leave the spec check idle.

For each selected directory, the validator reads the feature's spec files and the source inputs needed by their references. It checks structure before resolving IDs and checks cycles before computing waves. The workflow reports the validator's result in the pull request.

## Data and Interfaces

The workflow supplies repository-relative feature directory paths. The validator reads Markdown from those directories and the corresponding templates under `specs/templates/`, ticket text from the path under `tickets/` cited by the requirements file, and scenario tags from the adjacent `gherkin.feature`. Spec tables use bare IDs such as `S-012` while Gherkin uses tags such as `@S-012`. Task wave values are integers. Validation reads repository files and reports a status and diagnostic messages.

## Evidence Outcomes

A conforming pull request passes and the existing intake and Gherkin checks remain available. Legacy errors in an unrelated directory do not affect the result. Template-only, ticket-only, and Gherkin-only changes leave spec validation idle. Each structural, traceability, or dependency error in the Gherkin examples fails the check with the affected path and rule.
