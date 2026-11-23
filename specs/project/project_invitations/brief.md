# Intake Brief: Project Invitations

- **Issue:** #134 ([project-invitations])
- **Bounded Context:** project
- **User Story:** As a project owner, I can invite collaborators.

## Intent
Allow a project owner to send a project invitation to a collaborator by email with an assigned role, and allow the invited user to accept (or decline) the invitation to become a project member.

## Context & Existing Domain State
- ackend/domain/project/models/aggregates.py already defines Project.invite_member(member) and Project.members (list[Member]), while ackend/domain/project/models/value_objects.py defines Role (VIEWER = 0, EDITOR = 1) and Email.
- Currently, Project.invite_member(member) directly appends a Member without an invitation lifecycle (pending, ccepted, declined, evoked, expired).
- We need a persistent ProjectInvitation entity/aggregate (or sub-resource), repository persistence, application services (invite_collaborator, ccept_invitation, evoke_invitation, list_invitations), and HTTP endpoints under /api/projects.

## Scope
- Owner invites a user by email to a project with a target role (iewer or editor).
- Invited user views pending invitations and accepts an invitation to be added to Project.members with the invited role.
- Owner can view pending invitations for their project and revoke a pending invitation before acceptance.
- Prevent duplicate active invitations for the same email/project and prevent inviting users who are already project members or the project owner.

## Out of Scope
- Updating an existing member's role or removing an active member (covered under Issue #135 [project-member-management]).
- Discovering all shared projects across a user's workspace (covered under Issue #137 [shared-project-discovery]).
- Per-manuscript access role overrides (covered under Issue #118 [projects-manuscript-access]).

## Expected Outcomes
- An invited person who accepts becomes a project member with the specified role.
- Pending invitations can be listed and revoked by the project owner.
- Invalid, expired, revoked, or already-accepted invitations cannot be accepted again (400 / 404 / 409).

## Open Questions & Proposed Resolutions
1. **How should invitations be delivered, expire, or be revoked?**
   - **Delivery (Proposed):** Persist invitations in MongoDB and expose them in-app via GET /api/projects/invitations (for the invitee's email) alongside an invitation token/ID so invitations work immediately without blocking on external SMTP delivery.
   - **Expiration (Proposed):** Default expiration window of 7 days (expires_at = created_at + 7 days); attempting to accept after expires_at transitions/treats the invitation as expired and returns 400/410.
   - **Revocation (Proposed):** Project owners can revoke any pending invitation via DELETE /api/projects/<project_id>/invitations/<invitation_id> (or PATCH .../revoke), setting status to evoked so it can no longer be accepted.
