# Design: Identity & Access Management
Contract and Jira mapping: [requirements.md](requirements.md). This is a specification, not a repository audit. Paths come from Jira; verify existing code before adding files.

## Overview

Flask auth blueprint validates input with Pydantic, calls identity services, and serializes public fields. Shared error handlers translate domain failures; Flask-Limiter enforces auth limits.

## Architecture

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

Data and request flows:

- Account: id, display_name, email, password_hash. Public responses never expose password_hash.
- Session: account ID only; resolve identity from session, never a client-supplied account ID.
- Registration: validate -> check strength/uniqueness -> hash -> persist -> establish session -> respond.
- Login: validate -> lookup -> verify -> establish fresh session -> respond. Use the same failure response for unknown email and wrong password.
- Protected requests: login_required -> load account -> read/update/delete. Proposed handling for invalid, expired, or orphaned sessions: clear session and return 401.
- Logout: clear authentication state and cookie, even if already logged out.
- Delete: check owned projects -> remove memberships and account -> clear session. Proposed atomic transaction prevents partial deletion; project-owner rejection remains an assumption.

## Components and Interfaces

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

### Authentication session

The session is authentication state managed by the authentication service and Flask session infrastructure, rather than a separate domain entity in this design.

Its application data contains only the account ID. Protected operations use that ID to load the current account instead of accepting a client-supplied account ID. Login and registration establish the session; logout and successful account deletion clear it. Session storage and lifetime remain to be confirmed.

### Relationships

An account may own projects and have project memberships. Reuse existing project and membership models where available; their concrete fields and implementation require repository verification.

Account deletion removes the account's memberships and the account. The proposed transaction makes these changes atomic. Blocking deletion when the account owns projects remains an unconfirmed requirement; if confirmed, the deletion service checks ownership before making changes. Project transfer and project deletion remain outside this epic.

## Data Models

### Account entity fields

| Field | Type / constraint | Notes |
| --- | --- | --- |
| id | Repository's existing identifier type | Immutable. |
| display_name | String, 1–128 characters | Mutable via rename only. |
| email | String, 1–128 characters, unique | Exact normalization rules remain to be confirmed. |
| password_hash | Argon2 hash string | Plaintext password is never stored or logged. |

### Session payload

The session carries only the account ID. No additional fields are currently specified.

### Response shapes

- Registration and login responses: id, display_name.
- Current-account read and update responses: id, display_name, email.
- password_hash is never included in any response.

Exact field names and envelope format are not yet fully specified; confirm against the {error, code?} envelope decision in Implementation decisions below.

## Correctness Properties

### Property 1: Invalid credentials do not reveal account existence

For any login attempt with an unknown email or an incorrect password,
authentication fails with the same status and error body.

- Email uniqueness is enforced atomically in storage, not only by a prior lookup.
- Plaintext passwords are never persisted or logged at any point.
- Pydantic enforces 1–128 character limits; validation failure returns 400. Password-strength rejection is separate (422).
- Flask-Limiter applies a 5-request/minute/IP limit on registration and login; 429 responses include Retry-After.
- Cookies are configured HttpOnly, Secure, SameSite=Lax with an explicit development override.
- Unknown email and incorrect password produce the same authentication failure response (no enumeration).
- Protected operations resolve identity from the session, never from a client-supplied account ID.
- PATCH /api/auth/me is implemented once; THES-26 and proposed THES-186 describe the same route.
- Follow THES-184's JSON Content-Type gate and no-CSRF-token decision. Proposed deployment safeguard: same-origin requests, no permissive credentialed CORS.
- Confirm exact domain codes, password policy, email normalization, session lifetime/backend, and deletion ownership rule before finalizing code.

## Error Handling

- Domain failures are translated to HTTP responses by shared error handlers in bootstrap/error_handlers.py (verify path).
- All error responses use a centralized {error, code?} envelope, including framework errors and 415 responses. Proposed: add a details field for validation failures while preserving this envelope.
- Invalid, expired, or orphaned sessions: proposed handling clears the session and returns 401.
- Duplicate-email race conditions are resolved by the atomic storage uniqueness constraint; the service returns the appropriate domain failure.
- For bodyless logout, proposed client behavior sends Content-Type: application/json without requiring a parsed body.
- Retry-After header is included on rate-limit (429) responses.

## Testing Strategy

Test each R1–R9 success/failure contract. Include duplicate-email races, unauthenticated access, invalid/expired sessions, deletion rollback, cookie flags, rate-limit boundaries, and absence of password data in responses and logs. These additional edge cases are design recommendations and are not yet fully specified as test cases.
