# Requirements Analysis
## Identity & Access Management

**Project:** Theseus (THES)  
**Epic:** [THES-1](https://theseus-inc.atlassian.net/browse/THES-1) — Identity & Access Management  
**Prepared for:** Glen Suguitan  
**Date:** 7 November 2026  
**Status:** Review draft based on Jira; implementation not verified

This document covers only THES-1 and its five stories (THES-2, THES-10, THES-16, THES-20 and THES-24), including their 21 subtasks. Other Theseus epics are excluded. The source is the Jira issue snapshot retrieved on 7 November 2026; comments, attachments and repository code were not inspected. All 27 scoped issues were marked To Do, which is workflow metadata rather than proof of implementation status.

**Documented** identifies an explicit Jira requirement. **Proposed** identifies a design recommendation. **Open** identifies a detail Jira has not settled.

## 1. Purpose

The identity module allows a person to register an account, authenticate, inspect the current session, log out, and update their display name. It provides the authenticated identity that other Theseus modules can consume. Designing those other modules' permissions or workflows is outside this document.

The user-facing objectives are to gain access through a new account, return using existing credentials, know which account is active, end access on shared devices, and maintain a preferred display name.

## 2. Scope

| In scope — documented by THES-1 | Out of scope — documented by THES-1 |
|---|---|
| Registration with name, email and password | Password reset / forgotten-password flow |
| Login, logout and current-session inspection | Email verification |
| Password-strength enforcement and Argon2 hashing | OAuth / third-party login |
| Display-name updates | Role-based access control beyond project ownership |
| Session-cookie authentication | — |

Project-ownership workflows belong to a separate epic and are not designed here. Source-library, manuscript, version-control and AI-assistant requirements are also excluded.

## 3. Actors and interactions

| Actor | Interaction |
|---|---|
| New user | Registers with display_name, email and password; receives an authenticated session. |
| Returning user | Logs in using email and password. |
| Authenticated user | Inspects the session, updates their own display name and logs out. |
| Unauthenticated caller | May register, log in or safely call logout; cannot inspect or update a protected account. |
| Identity backend | Validates requests, persists account data, manages sessions and translates domain errors to HTTP responses. |

## 4. Functional requirements and acceptance criteria

The following five requirement groups preserve the Jira story descriptions and acceptance criteria. The linked subtasks define the corresponding implementation and verification work; their existence does not mean that work is complete.

### FR-01 — 1.1 Register an account

**Source:** [THES-2](https://theseus-inc.atlassian.net/browse/THES-2)  
**Epic:** [THES-1](https://theseus-inc.atlassian.net/browse/THES-1)

As a new user, I want to register with my name, email, and password, so that I can create an account and be logged in immediately.

Acceptance criteria:

* AC-1: Given valid display_name, email, and password (each 1–128 chars) and an email not already registered, when I POST /api/auth/register, then I receive 201 {"id", "display_name"} and a session cookie is set (auto-login).
* AC-2: Given an email that is already registered, when I register, then the response is 409 {"error": "...", "code": ...} and no account is created.
* AC-3: Given a password that fails the strength rules, when I register, then the response is 422 {"error": "..."}.
* AC-4: Given any field outside the 1–128 character limit, when I register, then the response is 400 with Pydantic validation details.
* AC-5: The endpoint is rate-limited to 5 requests/minute per IP.
* AC-6: The stored password is hashed with Argon2; the plaintext is never persisted.

**Supporting subtasks**

- [THES-3](https://theseus-inc.atlassian.net/browse/THES-3) — Implement create_account service: validate uniqueness, hash password (Argon2), persist account.
- [THES-4](https://theseus-inc.atlassian.net/browse/THES-4) — Implement register_user service: orchestrate account creation + session creation.
- [THES-5](https://theseus-inc.atlassian.net/browse/THES-5) — Add /api/auth/register blueprint route with Pydantic request model (1–128 char limits).
- [THES-6](https://theseus-inc.atlassian.net/browse/THES-6) — Map domain errors (EmailAlreadyRegistered, WeakPassword) to 409/422 in bootstrap/error_handlers.py.
- [THES-7](https://theseus-inc.atlassian.net/browse/THES-7) — Set the session cookie on success (auto-login).
- [THES-8](https://theseus-inc.atlassian.net/browse/THES-8) — Apply the 5/minute auth rate limit via Flask-Limiter.
- [THES-9](https://theseus-inc.atlassian.net/browse/THES-9) — Add tests: happy path, duplicate email, weak password, invalid lengths, rate limit.

### FR-02 — 1.2 Log in

**Source:** [THES-10](https://theseus-inc.atlassian.net/browse/THES-10)  
**Epic:** [THES-1](https://theseus-inc.atlassian.net/browse/THES-1)

As a returning user, I want to log in with my email and password, so that I can resume work on my manuscripts.

Acceptance criteria:

* AC-1: Given valid credentials, when I POST /api/auth/login, then I receive 200 {"id", "display_name"} and a session cookie is set.
* AC-2: Given an unknown email or a wrong password, when I log in, then the response is 401 {"error": "..."} (no distinction revealed between unknown email and wrong password).
* AC-3: Given fields outside 1–128 chars, then 400 with validation details.
* AC-4: The endpoint is rate-limited to 5 requests/minute per IP.

**Supporting subtasks**

- [THES-11](https://theseus-inc.atlassian.net/browse/THES-11) — Implement login_user service: verify password against Argon2 hash, create session.
- [THES-12](https://theseus-inc.atlassian.net/browse/THES-12) — Add /api/auth/login blueprint route with Pydantic request model.
- [THES-13](https://theseus-inc.atlassian.net/browse/THES-13) — Map InvalidCredentials to 401.
- [THES-14](https://theseus-inc.atlassian.net/browse/THES-14) — Apply 5/minute auth rate limit.
- [THES-15](https://theseus-inc.atlassian.net/browse/THES-15) — Add tests: valid login, wrong password, unknown email, invalid input, rate limit.

### FR-03 — 1.3 Inspect the current session

**Source:** [THES-16](https://theseus-inc.atlassian.net/browse/THES-16)  
**Epic:** [THES-1](https://theseus-inc.atlassian.net/browse/THES-1)

As a logged-in user, I want to see who I am currently logged in as, so that I can confirm my session is active and correct.

Acceptance criteria:

* AC-1: Given a valid session cookie, when I GET /api/auth/me, then I receive 200 {"id", "display_name", "email"}.
* AC-2: Given no session cookie, when I GET /api/auth/me, then 401 {"error": "Unauthorized"}.

**Supporting subtasks**

- [THES-17](https://theseus-inc.atlassian.net/browse/THES-17) — Implement get_account service: load account by session identity.
- [THES-18](https://theseus-inc.atlassian.net/browse/THES-18) — Add /api/auth/me route behind login_required.
- [THES-19](https://theseus-inc.atlassian.net/browse/THES-19) — Add tests: authenticated fetch, unauthenticated fetch.

### FR-04 — 1.4 Log out

**Source:** [THES-20](https://theseus-inc.atlassian.net/browse/THES-20)  
**Epic:** [THES-1](https://theseus-inc.atlassian.net/browse/THES-1)

As a logged-in user, I want to log out, so that my session ends and my account is protected on shared devices.

Acceptance criteria:

* AC-1: Given a valid session, when I POST /api/auth/logout, then I receive 204 and the session cookie is cleared.
* AC-2: Logging out does not require a body; calling it without a session is still safe.

**Supporting subtasks**

- [THES-21](https://theseus-inc.atlassian.net/browse/THES-21) — Implement session teardown in auth_service.py.
- [THES-22](https://theseus-inc.atlassian.net/browse/THES-22) — Add /api/auth/logout route.
- [THES-23](https://theseus-inc.atlassian.net/browse/THES-23) — Add tests: logout clears cookie, logout without session is a no-op success.

### FR-05 — 1.5 Update account details

**Source:** [THES-24](https://theseus-inc.atlassian.net/browse/THES-24)  
**Epic:** [THES-1](https://theseus-inc.atlassian.net/browse/THES-1)

As a user, I want to update my display name, so that my identity reflects my current preferred name.

Acceptance criteria:

* AC-1: Given a valid session and a new display_name (1–128 chars), when I update my account, then it is persisted and reflected in /api/auth/me.
* AC-2: Given no session, then 401.

**Supporting subtasks**

- [THES-25](https://theseus-inc.atlassian.net/browse/THES-25) — Implement update_account service.
- [THES-26](https://theseus-inc.atlassian.net/browse/THES-26) — Add account-update route (if not already exposed) with validation.
- [THES-27](https://theseus-inc.atlassian.net/browse/THES-27) — Add tests: update display name, invalid length, unauthenticated.

## 5. Data and validation requirements

| Data | Documented rule | Unresolved detail |
|---|---|---|
| Registration display_name | 1–128 characters | Trimming and whitespace-only values |
| Registration email | 1–128 characters; must not already be registered | Syntax and normalization policy |
| Registration password | 1–128 characters; must satisfy strength rules; Argon2-hashed | Exact strength rules and Argon2 settings |
| Login email/password | Each 1–128 characters | Missing/wrong-type input contract |
| Updated display_name | 1–128 characters; persisted and visible through /api/auth/me | Update endpoint and success response |
| Account ID | Included in registration, login and /me responses | Identifier type and representation |
| Session cookie | Set on successful registration/login; cleared on logout | Name, storage, expiry, attributes and revocation |

Passwords must never be persisted in plaintext (THES-2 AC-6). Hashes and session secrets are not part of the documented public account responses. Email/password changes are not requested by the account-update story; the update scope is display_name only.

## 6. Security and quality requirements

| ID | Requirement | Status and evidence |
|---|---|---|
| NFR-01 | Store Argon2 password hashes, never plaintext passwords. | Documented: THES-2, THES-3. |
| NFR-02 | Use the same login failure behavior for an unknown email and an incorrect password. | Documented: THES-10 AC-2. |
| NFR-03 | Limit registration and login to 5 requests/minute/IP. | Documented: THES-2 AC-5 and THES-10 AC-4. |
| NFR-04 | Protect /me and account updates with authentication; no session returns 401. | Documented: THES-16 and THES-24. |
| NFR-05 | Return Pydantic validation details for out-of-range registration/login fields. | Documented: THES-2 and THES-10. |
| NFR-06 | Logout without a session remains a no-op success. | Documented: THES-20 and THES-23. |
| NFR-07 | Use secure cookies, CSRF protection, server-side session invalidation and redacted logs. | Proposed; mechanisms need decisions D03 and D11. |
| NFR-08 | Prevent duplicate accounts under concurrent requests and partial registration writes. | Proposed implementation quality supporting uniqueness and auto-login. |
| NFR-09 | Specify measurable latency, availability and capacity targets. | Open; no numeric targets in the scoped Jira issues. |

## 7. Business rules and error outcomes

1. Successful registration creates an account and automatically establishes a session.
2. A duplicate email returns 409 and must not create another account.
3. A weak password returns 422; request length errors return 400.
4. Successful login returns the same account identity and establishes a session.
5. Unknown email and wrong password both return 401 without identifying which condition occurred.
6. /me returns only the current session's account details.
7. Logout returns 204, clears the session cookie and remains safe when no session exists.
8. Display-name updates apply to the current authenticated account and appear on the next /me read. Deriving the target from the session is a proposed implementation safeguard.

## 8. Dependencies and assumptions

Documented technologies and boundaries are Flask blueprint routes, Pydantic request models, Flask-Limiter, Argon2, identity domain services and cookie authentication. The account persistence engine and session backend are not established by the scoped issues. Do not assume a database engine, JWT implementation or existing frontend based on this document.

A repository review should locate the existing account-update route before adding one, as THES-26 explicitly allows it to already exist. Frontend forms consume the identity API but their framework and visual design are not specified.

## 9. Open decisions

| ID | Open detail | Proposed direction |
|---|---|---|
| D01 | Exact password-strength rules and Argon2 parameters | Agree a strength policy and tested hash configuration; the 1–128 character request limit does not itself define password strength. |
| D02 | Email syntax, normalization and case-insensitive uniqueness | Agree one normalization rule and enforce uniqueness atomically; preserve the intended display form. |
| D03 | Session backend, cookie name/attributes, expiry, renewal and revocation | Use an opaque cookie token backed by revocable server-side sessions; confirm before implementation. |
| D04 | Account-update route, HTTP method and success response | Propose PATCH /api/account with display_name and 204 success; inspect the repository first to avoid duplicating an existing route. |
| D05 | Invalid account-update length response and validation details | Propose 400 using the same request-validation contract as other identity routes. |
| D06 | Rate-limit response, window algorithm and trusted client-IP resolution | Propose 429 with Retry-After; document whether login and registration have separate 5/minute/IP buckets. |
| D07 | Error code values and error-body schema | Define stable codes while retaining Jira's error field and Pydantic validation details. |
| D08 | Partial registration failure after account persistence but before session creation | Propose account/session atomic creation where supported; otherwise define a recoverable response and login path without creating duplicate accounts. |
| D09 | Email/display-name trimming, missing fields and wrong JSON types | Define validation explicitly; do not infer whitespace rejection solely from minimum length. |
| D10 | Performance, availability, retention and session storage capacity | Set measurable targets with the team; Jira provides no numeric service targets. |
| D11 | CSRF protection, HTML output escaping and logging policy | Apply CSRF protection to cookie-authenticated mutations; escape display names on rendering; redact credentials and session tokens. |


## 10. Acceptance and test traceability

| Requirement | Verification issue | Minimum checks |
|---|---|---|
| FR-01 Registration | [THES-9](https://theseus-inc.atlassian.net/browse/THES-9) | Successful account/session creation; duplicate email; weak password; lengths; rate limit; stored hash. |
| FR-02 Login | [THES-15](https://theseus-inc.atlassian.net/browse/THES-15) | Valid credentials; wrong password; unknown email; invalid input; rate limit. |
| FR-03 Current session | [THES-19](https://theseus-inc.atlassian.net/browse/THES-19) | Authenticated account response; missing-session 401. |
| FR-04 Logout | [THES-23](https://theseus-inc.atlassian.net/browse/THES-23) | Cookie cleared; session teardown; no-session no-op success. |
| FR-05 Display-name update | [THES-27](https://theseus-inc.atlassian.net/browse/THES-27) | Successful update reflected in /me; invalid length; missing-session 401. |

Use 0, 1, 128 and 129 characters to exercise documented length boundaries. Use a policy-compliant password for successful boundary tests so strength rules do not obscure length validation. For non-password fields, also test missing and wrong-type values after D09 is agreed.

Proposed additional tests: two simultaneous registrations with one email; replay of a revoked session; updating another account by injecting an ID; credential/token redaction; CSRF rejection; account persistence when session creation fails. These supplement the Jira tests and should not be presented as original acceptance criteria.

**Proposed completion gate:** all five stories' documented criteria pass; the open decisions affecting implementation are resolved; the API contract and tests agree; the implemented behavior is reviewed against the repository. No implementation tests were run while authoring this analysis.

## 11. References

Primary epic: [THES-1](https://theseus-inc.atlassian.net/browse/THES-1). Story and subtask links are embedded in section 4. This file and the companion **THES-1_Specification_Design.md** replace the earlier project-wide drafts. No Jira content was changed.

