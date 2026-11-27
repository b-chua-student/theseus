# [projects-manuscript-access] As a Theseus user, I can have different access roles for different manuscripts

## Intent

Let a user edit one manuscript and have view-only access to another within Projects.

## Context

This ticket covers user access to manuscripts in Projects.

## Scope

- Apply each user's role separately for each manuscript.

## Expected Outcomes

- [ ] Given User 1 has edit access to Manuscript 1 and view-only access to Manuscript 2, they can edit Manuscript 1 and view Manuscript 2. An attempt to edit Manuscript 2 leaves it unchanged.

## Rules / Constraints

- A user's role on a manuscript determines whether they can edit that manuscript.

## Non-Functional Requirements

None specified.

## Out of Scope

No exclusions specified.

## Open Questions

- Who assigns and changes manuscript roles?
- What access should a user have when no role is assigned for a manuscript?

## Output Paths

- Intake brief: `specs/manuscript/per_manuscript_access/brief.md`
- Gherkin: `specs/manuscript/per_manuscript_access/gherkin.feature`
- Spec files: `requirements.md`, `design.md`, and `tasks.md` in `specs/manuscript/per_manuscript_access/`.

## Definition of Done

- [ ] Intake generated and approved
- [ ] Gherkin generated and approved
- [ ] Open questions resolved
- [ ] Spec, Gherkin, and code in sync
- [ ] Reviewed and merged
