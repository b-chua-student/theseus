# Intake Brief: Shared Project Discovery (#137)

## Goal
Allow authenticated users to discover and open both projects they own and projects shared with them in a unified project list (`GET /api/projects`) with optional `scope` filtering (`all`, `owned`, `shared`), ownership indicators, and effective role visibility.

## In Scope
- Extend project query/repository filtering (`backend/domain/project/`) to match projects where the authenticated user is either `Project.owner_id` or a `Member` (`Member.id` of type `MemberId` in `Project.members`).
- Update `GET /api/projects` to accept optional `?scope=all|owned|shared` (default `all`, `400` on invalid scope) and return `ownership` (`owned` or `shared`) and effective `role` (`owner`, `editor`, or `viewer`) for each project.
- Enforce membership authorization on `GET /api/projects/<project_id>` so owners and active members receive project details (`200`) with their effective role, while non-members or removed members receive `403` without leaking project metadata.
- Frontend workspace project list support displaying shared projects alongside owned projects with scope filter controls.

## Non-Goals
- Sending or accepting project invitations (covered in #134).
- Updating member roles or removing members (covered in #135).
- Per-manuscript role overrides (covered in #118).

## Constraints
- Follow DDD/Clean Architecture layers (`models/`, `services/`, `infrastructure/`, `api/`) with zero framework imports inside `domain/project/models/`.
- Require authentication (`@login_required` -> `401` if unauthenticated) on all endpoints.
- Pending invitations must not expose projects in `GET /api/projects` until accepted; `403` responses must never reveal project title or owner.

## Success Criteria
- `GET /api/projects` (default `scope=all`) returns owned and shared projects without duplicates, including `ownership` and effective `role`.
- `GET /api/projects?scope=shared` returns only shared projects (empty list `200` if user only owns projects), and `?scope=owned` returns only owned projects.
- Active collaborators can open shared project details via `GET /api/projects/<project_id>` (`200`), while non-members and removed members receive `403` without leaked metadata.

## Open Questions & Proposed Resolutions
1. **Unified list vs. separate view:** Return owned and shared projects in a single unified `GET /api/projects` endpoint with `ownership` (`owned`/`shared`) and an optional `?scope=all|owned|shared` filter (default `all`).
2. **Non-member detail response:** Return `403 Forbidden` with a generic error payload (no project title or owner details leaked) when a signed-in non-member requests `GET /api/projects/<project_id>`.
