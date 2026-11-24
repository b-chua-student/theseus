# Intake Brief: Per-Manuscript Access (#118)

## Goal
Allow project owners to assign per-manuscript access roles (`editor` or `viewer`) to project members so a collaborator can hold different permissions on different manuscripts within the same project.

## In Scope
- `ManuscriptRoleAssignment` / per-manuscript role rules in `backend/domain/manuscript/` supporting manuscript-level `editor` and `viewer` overrides alongside project-level `owner`, `editor`, and `viewer` roles (#135).
- Precedence rules: project `owner` always retains full edit/manage access across all manuscripts and cannot be demoted; project members with a manuscript override use their manuscript role (`editor` or `viewer`), while roleless members fall back to their baseline project role (`editor` or `viewer`).
- Owner-only endpoints to assign, update, or revoke a project member's role on a specific manuscript (`PUT`/`DELETE /api/projects/<project_id>/manuscripts/<manuscript_id>/roles/<member_id>`).
- Enforce per-manuscript write checks on manuscript edit endpoints (`403` for `viewer` or non-member, leaving manuscript content unchanged) and revoke manuscript overrides if a member is removed from the project.

## Non-Goals
- Project-level invitations (#134), project-level member management (#135), or shared project discovery (#137).
- Public link sharing outside project membership (deferred).

## Constraints
- Follow DDD/Clean Architecture layers (`models/`, `services/`, `infrastructure/`, `api/`) with zero framework imports inside `domain/manuscript/models/`.
- Require authentication (`@login_required` -> `401` if unauthenticated) on all endpoints.
- Access on one manuscript must never leak to another manuscript in the same or another project.

## Success Criteria
- A project member with `editor` on Manuscript 1 and `viewer` on Manuscript 2 can edit Manuscript 1 (`200`) and view Manuscript 2 (`200`), while attempting to edit Manuscript 2 returns `403` and leaves content unchanged.
- Project `owner` can assign or change per-manuscript `editor`/`viewer` roles (`200`/`204`), whereas non-owners (including manuscript `editor`s) receive `403`.
- Members without a manuscript-specific override inherit their baseline project role (`editor` or `viewer`), and non-members receive `403`.

## Open Questions & Proposed Resolutions
1. **Who assigns and changes manuscript roles:** Only the project `owner` (#135) can assign, update, or revoke per-manuscript roles; project `owner` access cannot be restricted or demoted.
2. **Reconciliation with project roles (#135) & default fallback:** Project roles (`owner`, `editor`, `viewer`) provide the baseline; per-manuscript assignments (`editor`, `viewer`) override the baseline for that specific manuscript, and roleless members fall back to their project role.
