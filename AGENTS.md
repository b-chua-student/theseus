# AGENTS.md

## Workflow
Ticket → Intake & Gherkin → Spec Files (requirements.md, design.md, tasks.md) -> Implementation

The ticket is the source input. Everything else is derived from it.

## Templates
- Ticket: `specs/templates/ticket.md`
- Intake: `specs/templates/intake.md`
- Gherkin: `specs/templates/feature.feature`
- Requirements: `specs/templates/requirements.md`
- Design: `specs/templates/design.md`
- Tasks: `specs/templates/tasks.md`

Human-facing issue template: `.github/ISSUE_TEMPLATE/sdd-ticket.md`

## Output Paths
Each feature lives in `specs/<context>/<feature_name>/`.

- Intake brief: `brief.md`
- Gherkin: `gherkin.feature`
- Spec files: `requirements.md`, `design.md`, and `tasks.md`

## Creating a Ticket
1. Read `specs/templates/ticket.md`.
2. Fill it in from the request. Remove all HTML comments.
3. Save to `tickets/<ID>.md`.
4. Create the issue:
   ```bash
   gh issue create --title "<title>" --body-file tickets/<ID>.md --label spec
   ```

## Generating Intake and Gherkin
1. Read the ticket (`tickets/<ID>.md`, or `gh issue view <number>`).
2. Generate the intake from `specs/templates/intake.md`.
3. Generate the Gherkin from the intake, using `specs/templates/feature.feature`.
4. Stop for approval before proceeding to spec files or implementation.

## Generating Spec Files

After intake and Gherkin approval, fill in the three spec templates in the feature directory alongside `brief.md` and `gherkin.feature`. Preserve the template headings, table columns, and existing IDs.

1. In `requirements.md`, include one source entry in the form ``- Ticket: `tickets/<ID>.md` ``. If the source is a GitHub issue, save its body under `tickets/` before citing it. Give each verifiable requirement an `R-###` ID, set its Source to `from ticket`, and cite the actual nonblank ticket line numbers. Reference the relevant Gherkin IDs as `S-###` without the `@`, or use `-` when no scenario applies.
2. In `design.md`, assign each decision a `D-###` ID, name the affected components, and reference the requirements it supports. Cover every requirement.
3. In `tasks.md`, assign each task a `T-###` ID and reference the applicable requirements or design decisions. Cover every design decision with a task and every scenario with a verification task. Separate multiple IDs with commas and use `-` for empty dependencies or scenarios.
4. Keep the Mermaid dependency graph aligned with the task table, including standalone tasks. Draw arrows from prerequisite to dependent, check for cycles, and put independent tasks in wave 1. Set each dependent task's wave to one after its latest prerequisite.

## Rules
- Every requirement must trace to a line in the ticket.
- Anything not in the ticket goes under Open Questions as a suggestion, never as a requirement.
- No implementation details (routes, libraries, schemas) in tickets, intake, or Gherkin.
- Respect Out of Scope. Do not expand it.
- Do not modify approved specs without updating the ticket first.
- Behavior changes update the ticket, then intake, Gherkin, spec files, and code in that order.

## Implementation
- Follow the prerequisites and verification in `tasks.md`.
- Write step definitions before application code.
- All scenarios in the `.feature` file must pass.
- Keep spec, Gherkin, and code in sync.
