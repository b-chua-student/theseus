# Intake Brief: Project Member Management (#135)

## Goal
Allow project owners and existing project members to view a project's member list, while restricting role updates (`editor` or `viewer`) and member removals strictly to the project owner.

## In Scope
- Domain rules on `Project` (`backend/domain/project/models/`) supporting `owner`, `editor`, and `viewer` roles while blocking owner self-removal, owner self-demotion, and assigning `owner` via member-role updates.
- Application services (`ListMembersService`, `UpdateMemberRoleService`, `RemoveMemberService`) enriching member records via `IdentityAPI` (`UserDTO`).
- REST endpoints: `GET /api/projects/<project_id>/members` (owner or existing project member), `PATCH /api/projects/<project_id>/members/<member_id>` (owner only), and `DELETE /api/projects/<project_id>/members/<member_id>` (owner only).
- Validation for invalid/missing/case-mismatched roles (`400`), non-owner mutations (`403`), non-member reads (`403`), and unknown project or target member (`404`).

## Non-Goals
- Sending or accepting project invitations (covered in #134).
- Ownership transfer workflows (deferred).
- Per-manuscript role overrides (covered in #118).

## Constraints
- Follow DDD/Clean Architecture layers (`models/`, `services/`, `infrastructure/`, `api/`) with zero framework imports inside `domain/project/models/`.
- Require authentication (`@login_required` -> `401` if unauthenticated) on all endpoints.
- Removed members immediately lose project access; repeat removal returns `404`.

## Success Criteria
- Project owners and current project members can retrieve the member list (`200`); non-members receive `403`.
- Project owner can update a non-owner member's role between `editor` and `viewer` (`204`, idempotent if unchanged) and remove non-owner members (`204`).
- Non-owners attempting to update roles or remove members receive `403`.
- Attempts to remove the owner, demote the owner, or assign `owner` role are rejected (`400`/`403`).

## Open Questions & Proposed Resolutions
1. **Assignable roles & Owner clarity:** Project roles are `owner`, `editor`, and `viewer`; owners can assign `editor` or `viewer` to members, and cannot remove or demote themselves.
2. **Member-list read access:** Both project owners and existing project members can view the member list (`200`); non-members receive `403`.
