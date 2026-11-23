# Intake Brief: Project Member Management

- **Issue:** #135 (`[project-member-management]`)
- **Bounded Context:** `project`
- **User Story:** As a project owner, I can manage project members.

## Intent
Allow a project owner to view the current members of their project, update a member's project role, and remove a member from the project.

## Context & Existing Domain State
- `backend/domain/project/models/aggregates.py` already defines `Project.members` (`list[Member]`), `Project.edit_role(member, role)`, and `Project.remove_member(member)`.
- `backend/domain/project/models/value_objects.py` defines `Role` with `VIEWER = 0` and `EDITOR = 1`.
- `GET /api/projects/<project_id>` already returns the `members` array (`id`, `display_name`, `email`, `role`).
- Missing pieces to expose this capability: dedicated application services, request validation models, HTTP endpoints (`GET /<project_id>/members`, `PATCH /<project_id>/members/<member_id>/role`, `DELETE /<project_id>/members/<member_id>`), and corresponding unit/API tests.

## Scope
- View current project members for an existing project.
- Change an existing project member's role (`viewer` or `editor`).
- Remove an existing project member from the project.
- Enforce owner-only authorization and prevent removing or demoting the project owner via member management endpoints.

## Out of Scope
- Inviting new collaborators and accepting invitations (covered under Issue #134 `[project-invitations]`).
- Listing shared projects for non-owner members (covered under Issue #137 `[shared-project-discovery]`).
- Per-manuscript access role overrides (covered under Issue #118 `[projects-manuscript-access]`).

## Expected Outcomes
- An owner can view all current members of a project and their assigned roles.
- An owner can update a member's role between `viewer` and `editor`.
- An owner can remove a member from the project.
- Non-owners or unauthenticated callers are rejected (`401` / `403`), and unknown projects or members return `404`.

## Open Questions & Proposed Resolutions
1. **Which project roles should owners be able to assign?**
   - **Proposed Answer:** `viewer` (`Role.VIEWER`) and `editor` (`Role.EDITOR`), matching the existing `Role` enum in `domain/project/models/value_objects.py`. Ownership transfer remains a separate explicit action (`PATCH /api/projects/<project_id>/owner`).
2. **Can a non-owner member view the project member list, or only the owner?**
   - **Proposed Answer:** Project owners and existing project members can view the member list (`GET /api/projects/<project_id>/members`), while only the project owner can change roles or remove members.
