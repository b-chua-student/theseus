# Feature intake — Email verification

Draft submitted 2026-11-23. Product, Engineering and Security approval is pending.

## Goal

Confirm control of the address supplied at registration. A new user can sign in and browse their workspace while waiting for the email.

## In Scope

Registration, delivery and retry, confirmation, resend, audit logging and server-enforced workspace restrictions are in scope. The release decisions below are proposed for approval.

## Non-Goals

Changing an existing login address is a follow-up. It requires a pending address, collision handling at confirmation, and retaining the active login address until confirmation. The current User.change_email() immediately replaces the address. Password recovery, marketing, disposable-domain filtering, SMS, MFA, social login and support tooling are outside this release.

## Constraints

### Identity and rollout

Keep the existing registration inputs (display name, email and password), normalized unique email, 201 response and signed-in session. Persist the aggregate's verified boolean. New accounts start unverified. Record proof only after successful confirmation.

Before enabling restrictions, migrate pre-rollout accounts to a distinct legacy exemption. They retain existing workspace access without being reported as verified. Coordinate migration and registration so every post-cutover account receives the new policy. Implement and test persistence in PostgreSQL and MongoDB, with equivalent behavior in the in-memory adapter. A missing field on a newly created record must never grant an exemption.

Registration, login and GET /api/auth/me return verified and verification_required alongside existing response fields. The latter is true for unverified, non-exempt users. The app fetches /api/auth/me on authenticated startup and refresh. The server checks current account state on each restricted request.

## Workspace access

Signed-in users may read their authorized projects, manuscripts, sources, revisions, drafts and assistant conversations. Users requiring verification can sign out and resend. Show a verification banner and a read-only workspace. Enforce the same policy for direct API requests.

For accounts requiring verification, reject project, manuscript, source, revision, draft and assistant conversation mutations with 403 and error code email_verification_required before any side effect. This includes creating projects, uploading sources, editing sections, restoring revisions, switching drafts and sending assistant exchanges. Anonymous workspace requests continue to receive 401. Verification preserves existing ownership and authorization checks.

## Delivery and links

Integrate a transactional email sender, verification template and durable retry worker. Successful registration commits the account and pending delivery together. Retry transient failures across restarts, alert on exhausted retries, and suppress superseded deliveries. Target p95 dispatch within 30 seconds while the provider is healthy. Configure the sender domain and HTTPS application origin before rollout.

A public /verify-email landing page accepts direct navigation in a fresh browser. Opening the email link renders a confirmation control. Only explicit confirmation submits the token and consumes it. The token identifies the registration independently of the browser session. Confirmation neither signs the visitor in nor switches their session.

Use cryptographically random tokens of at least 128 bits, store only the token hash in verification records, compare hashes in constant time, and exclude raw tokens and addresses from application logs. Protect delivery payloads during retry. Expiry defaults to 24 hours from issuance and is configurable. Atomically consume the active token and persist verification. Report reused, expired, superseded and unrecognized links distinctly. A used token takes precedence over account status. Offer resend guidance on failure.

## Resend and audit

Authenticated resend targets the signed-in account. Public resend accepts a normalized email address and always returns the same acknowledgement for unknown, verified, throttled and eligible addresses. For eligible accounts, allow up to three accepted resends per rolling hour, at least 60 seconds apart. Initial delivery and provider retries do not count as resends. Enforce limits per account across both entry points. Only an accepted resend invalidates the prior token and queues its replacement.

Record sent, resent, verified, failed and rate-limited events with timestamps. Include the user ID when the account is known. Leave it absent for unknown tokens. Landing and resend pages must meet WCAG 2.1 AA and use the application's supported locales.

## Success Criteria

Target at least 70% confirmed within 24 hours, median confirmation under five minutes, bounces below 2%, 30% fewer missing-email support tickets and 40% fewer abusive registrations against baseline. Aim for a user who already has the email to finish in under a minute.

Acceptance scenarios are in [gherkin.feature](gherkin.feature).
