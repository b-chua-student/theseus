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

## Domain entities design

The following entity and method names are proposed design contracts. Verify existing models before implementation. This section elaborates the requirements without resolving their open decisions.

### Account

Account is the main identity entity. It represents a registered user and maintains account data independently of HTTP requests and session handling.

| Field | Purpose |
| --- | --- |
| id | Unique account identifier; use the repository's existing identifier type. |
| display_name | User's display name, restricted to 1–128 characters. |
| email | Login email, restricted to 1–128 characters and unique across accounts. Exact validation and normalization rules remain to be confirmed. |
| password_hash | Argon2 password hash. Plaintext passwords are never stored on the entity. |

### Proposed account methods

| Method | Responsibility |
| --- | --- |
| Account(id, display_name, email, password_hash) | Construct an account using validated data and an already hashed password. Enforce agreed domain field rules. |
| rename(display_name) | Validate the 1–128 character limit and update the display name. The calling service persists the change. |

Email and password changes are outside this feature's current scope, so no methods for those operations are proposed.

### Domain rules and service responsibilities

- Account identity remains unchanged when the display name changes.
- Account creation checks email uniqueness through the repository; storage must also enforce uniqueness atomically.
- The creation service checks password strength and hashes the password with Argon2 before constructing the account. Exact strength rules remain to be confirmed.
- The login service verifies the supplied password against the stored hash. Unknown email and incorrect password produce the same authentication failure response.
- Response serialization explicitly selects public fields and never includes password_hash.
- Registration and login return id and display_name. Current-account read and the proposed update response also include email.
- Account deletion is coordinated by a service and repository transaction, rather than an entity deleting itself. Atomic deletion is a design recommendation.

### Relationships

An account may own projects and have project memberships. Reuse existing project and membership models where available; their concrete fields and implementation require repository verification.

Account deletion removes the account's memberships and the account. The proposed transaction makes these changes atomic. Blocking deletion when the account owns projects remains an unconfirmed requirement; if confirmed, the deletion service checks ownership before making changes. Project transfer and project deletion remain outside this epic.

### Authentication session

The session is authentication state managed by the authentication service and Flask session infrastructure, rather than a separate domain entity in this design.

Its application data contains only the account ID. Protected operations use that ID to load the current account instead of accepting a client-supplied account ID. Login and registration establish the session; logout and successful account deletion clear it. Session storage and lifetime remain to be confirmed.

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

