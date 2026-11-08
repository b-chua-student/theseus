# Design: Identity & Access Management
Contract and Jira mapping: [requirements.md](requirements.md). This is a specification, not a repository audit. Paths come from Jira; verify existing code before adding files.

## Structure
Flask auth blueprint validates input with Pydantic, calls identity services, and serializes public fields. Shared error handlers translate domain failures; Flask-Limiter enforces auth limits.

| Jira service path | Responsibility |
| --- | --- |
| domain/identity/services/account/create_account.py | Check email uniqueness, validate password strength, hash with Argon2, persist account. |
| domain/identity/services/auth/register_user.py | Orchestrate account creation and automatic login. |
| domain/identity/services/auth/login_user.py | Verify credentials against Argon2 hash and establish session. |
| domain/identity/services/account/get_account.py | Load current account using session identity. |
| domain/identity/services/account/update_account.py | Update current account's display name only. |
| domain/identity/services/auth_service.py | Shared session creation/teardown and authentication support. |
| bootstrap/error_handlers.py | Central error-response helper and handler registration; verify path. |

Deletion service location is proposed: domain/identity/services/account/delete_account.py. Reuse existing repository/storage interfaces; no new database is prescribed.

## Data and request flow
- Account: id, display_name, email, password_hash. Public responses never expose password_hash.
- Session: account ID only; resolve identity from session, never a client-supplied account ID.
- Registration: validate -> check strength/uniqueness -> hash -> persist -> establish session -> respond.
- Login: validate -> lookup -> verify -> establish fresh session -> respond. Use the same failure response for unknown email and wrong password.
- Protected requests: login_required -> load account -> read/update/delete. Proposed handling for invalid, expired, or orphaned sessions: clear session and return 401.
- Logout: clear authentication state and cookie, even if already logged out.
- Delete: check owned projects -> remove memberships and account -> clear session. Proposed atomic transaction prevents partial deletion; project-owner rejection remains an assumption.

## Implementation decisions
- Enforce uniqueness atomically in storage, not only with an earlier lookup.
- Reuse existing Argon2 configuration; never persist or log plaintext passwords.
- Apply Pydantic 1–128 character limits and return 400 validation failures. Strength rejection is separate (422).
- Use Flask-Limiter for 5/minute/IP on registration and login; include Retry-After on 429.
- Centralize {error, code?} responses, including framework errors and 415. Proposed validation payload: add details while preserving this envelope.
- Configure HttpOnly, Secure, SameSite=Lax and an explicit development override. Confirm session backend and lifetime before claiming expiration/revocation behavior.
- Follow THES-184's JSON Content-Type gate and no-CSRF-token decision. Proposed deployment safeguard: same-origin requests, no permissive credentialed CORS.
- For bodyless logout, proposed client behavior sends Content-Type: application/json without parsing a required body.
- Implement PATCH /api/auth/me once; THES-26 and proposed THES-186 describe the same route.
- Confirm exact domain codes, password policy, email normalization, session lifetime/backend, and deletion ownership rule before finalizing code.

## Verification
Test each R1–R9 success/failure contract. Include duplicate-email races, unauthenticated access, invalid/expired sessions, deletion rollback, cookie flags, rate-limit boundaries, and absence of password data in responses/logs. These additional edge cases are design recommendations.

