# Intake Brief: Project Invitations (#134)

## Goal
Allow a project owner to invite collaborators to a project by email with a target role (`editor` or `viewer`), revoke pending invitations, and allow invited users to accept valid invitations to become project members.

## In Scope
- `ProjectInvitation` domain model in `backend/domain/project/` with statuses (`pending`, `accepted`, `revoked`, `expired`), unique single-use token, normalized lowercase email, role (`editor` or `viewer`), and 7-day expiry.
- Owner-only endpoints to create (`POST /api/projects/<project_id>/invitations`), list (`GET /api/projects/<project_id>/invitations`), and revoke (`DELETE /api/projects/<project_id>/invitations/<invitation_id>`) invitations.
- Invitee endpoint to accept a pending invitation (`POST /api/projects/invitations/<token>/accept`), appending a `Member` via `Project.add_member(new_member)`.
- Validation for invalid emails/roles (`400`), duplicate pending invites or inviting owner/existing members (`409`), email mismatch (`403`), and expired/revoked/reused tokens (`410`).

## Non-Goals
- Declining an invitation by an invitee (deferred).
- Automated outbound SMTP email delivery (system generates shareable invite token/link; email dispatch is deferred).
- Ownership transfer or post-join member role edits (covered in #135).

## Constraints
- Follow DDD/Clean Architecture layers (`models/`, `services/`, `infrastructure/`, `api/`) with zero framework imports inside `domain/project/models/`.
- All endpoints require an authenticated user (`@login_required` -> `401` if unauthenticated).
- Invitation tokens must be cryptographically unguessable, single-use, and never leak project details on unauthorized access.

## Success Criteria
- Project owner can create an invitation (`201`) returning invitation ID and token; non-owners receive `403`.
- Invited user matching the normalized email accepts a valid pending token (`200`) and is added via `Project.add_member(new_member)`.
- Revoked or expired invitations return `410` on accept; revoking an already-accepted invitation returns `409` and re-revoking is idempotent (`204`).
- Duplicate active invitations or invitations to existing members/owners return `409`; re-inviting after revoke/expiry succeeds (`201`).

## Open Questions & Proposed Resolutions
1. **Delivery, expiry, and revocation:** Return token/link directly in `201` response; expire after 7 days; owner can revoke pending invites (`204` idempotent if already revoked).
2. **Unregistered invitees & status codes:** Allow inviting unregistered emails (claimable after signup with matching email); return `410 Gone` for expired/revoked tokens.
