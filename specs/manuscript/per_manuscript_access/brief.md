# Intake Brief: Per-Manuscript Access Roles

- **Issue:** #118 ([projects-manuscript-access])
- **Bounded Context:** manuscript (integrating with project)
- **User Story:** As a Theseus user, I can have different access roles for different manuscripts.

## Intent
Let a user edit one manuscript and have view-only (or no) access to another manuscript within Projects by applying access roles separately per manuscript.

## Context & Existing Domain State
- ackend/domain/project/models/aggregates.py stores project-level membership (Project.members with Role.VIEWER or Role.EDITOR), while ackend/domain/manuscript/ manages manuscript entities linked to a project (project_id).
- Currently, manuscript read/write endpoints only verify project-level ownership or membership rather than manuscript-specific role assignments.
- We need a per-manuscript access mapping (ManuscriptAccess / manuscript_roles keyed by (manuscript_id, user_id) with Role.VIEWER or Role.EDITOR) and authorization checks on manuscript read and edit operations.

## Scope
- Store and evaluate access roles (iewer, editor) separately per manuscript for project collaborators.
- Allow a user with editor access on Manuscript A to view and edit Manuscript A, while restricting the same user with iewer access on Manuscript B to read-only access (rejecting edits with 403).
- Allow the project owner to assign or update per-manuscript roles (iewer, editor, or 
one) for project members.
- Project owners retain full editor access across all manuscripts in their project.

## Out of Scope
- Inviting new collaborators to a project (covered under Issue #134 [project-invitations]).
- Project-wide member removal or project-level role updates (covered under Issue #135 [project-member-management]).
- Listing shared projects across a workspace (covered under Issue #137 [shared-project-discovery]).

## Expected Outcomes
- Given User 1 has edit access to Manuscript 1 and view-only access to Manuscript 2, they can edit Manuscript 1 and view Manuscript 2; an attempt to edit Manuscript 2 fails (403) and leaves Manuscript 2 unchanged.
- A user's role on a manuscript determines whether they can edit that manuscript.

## Open Questions & Proposed Resolutions
1. **Who assigns and changes manuscript roles?**
   - **Proposed Resolution:** Only the project owner can assign, update, or revoke per-manuscript roles (PUT /api/projects/<project_id>/manuscripts/<manuscript_id>/access/<user_id>) for existing project members.
2. **What access should a user have when no role is assigned for a manuscript?**
   - **Proposed Resolution:** Fall back to the user's project-level membership role (Project.members: editor can edit, iewer can view); if the user is not a project member (or is explicitly restricted to 
one), deny access (403).
