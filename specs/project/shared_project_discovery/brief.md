# Intake Brief: Shared Project Discovery

- **Issue:** #137 ([shared-project-discovery])
- **Bounded Context:** project
- **User Story:** As a collaborator, I can find projects shared with me.

## Intent
Show projects where the signed-in user is a member in the project workspace so collaborators can discover and open shared projects.

## Context & Existing Domain State
- ackend/domain/project/models/aggregates.py defines Project with owner_id: UUID and members: list[Member], where each Member holds user_id: UUID and ole: Role (VIEWER or EDITOR).
- Currently, ProjectRepository and project listing endpoints only filter by owner_id (or need a membership query ind_by_member_id(user_id) / unified list_accessible_projects(user_id)).
- Collaborators who accept a project invitation need a reliable way to list and open projects shared with them, along with their effective role (owner, editor, or iewer).

## Scope
- Query and return all non-deleted projects where the authenticated user is listed in Project.members (and optionally unify with owned projects via a relationship/role indicator).
- Allow a collaborator who is a member of a shared project to open/retrieve that project (GET /api/projects/<project_id>), while returning 403 or 404 for users who are neither owner nor member.
- Include the signed-in user's role (owner, editor, iewer) in the project summary response so the frontend workspace can filter or badge shared projects cleanly.

## Out of Scope
- Inviting collaborators or accepting invitations (covered under Issue #134 [project-invitations]).
- Adding, updating, or removing project members (covered under Issue #135 [project-member-management]).
- Per-manuscript access role overrides (covered under Issue #118 [projects-manuscript-access]).

## Expected Outcomes
- A collaborator can find and open a project they joined from their project list.
- Users who are neither the owner nor a member of a project cannot view or open it.

## Open Questions & Proposed Resolutions
1. **Should shared projects appear in the same list as owned projects or in a separate view?**
   - **Proposed Resolution:** Return a unified list from GET /api/projects containing both owned and shared projects, enriched with ownership (owned | shared) and current_user_role (owner | editor | iewer), plus an optional query filter ?scope=all|owned|shared (default ll) so the UI can render either a combined workspace list or separate "Owned" / "Shared with me" tabs from a single endpoint.
