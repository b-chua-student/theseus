# AGENTS.md

## Workflow
Ticket → Intake & Gherkin → Spec Files (requirements.md, design.md, tasks.md) -> Implementation

The ticket is the source input. Everything else is derived from it.

## Templates
- Ticket: `specs/templates/ticket.md`
- Intake: `specs/templates/intake.md`
- Gherkin: `specs/templates/feature.feature`

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
4. Stop and wait for approval before writing code.

## Rules
- Every requirement must trace to a line in the ticket.
- Anything not in the ticket goes under Open Questions as a suggestion, never as a requirement.
- Tag each requirement as `from ticket` or `assumed`.
- No implementation details (routes, libraries, schemas) in tickets, intake, or Gherkin.
- Respect Out of Scope. Do not expand it.
- Do not modify approved specs without updating the ticket first.
- Behavior changes update the ticket, then intake, then Gherkin, then code.

## Implementation
- Write step definitions before application code.
- All scenarios in the `.feature` file must pass.
- Keep spec, Gherkin, and code in sync.
