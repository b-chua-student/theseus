# Requirements Document

## Introduction

Source: [THES-1](https://theseus-inc.atlassian.net/browse/THES-1), direct children and their listed subtasks, read 2026-11-08.
Owner: Glen Rae Ruiz Suguitan. Scope: this epic only. Jira calls it THES-1; its description retains legacy THESEUS-1.

**Exclusions:** Password reset, email verification, OAuth/third-party login, and roles beyond project ownership. Account deletion is included because it is now a direct child of THES-1.

## Glossary

Not specified.

## Requirements

| ID | Jira | Required behavior |
| --- | --- | --- |
| R1 | THES-2 | POST /api/auth/register accepts display_name, email, password, each 1–128 characters. Valid unique email: create account, return 201 {id, display_name}, set session cookie. Duplicate email: 409; weak password: 422; invalid input: 400 with validation details. |
| R2 | THES-10 | POST /api/auth/login accepts email/password, each 1–128 characters. Valid credentials: 200 {id, display_name} and session cookie. Unknown email/wrong password: identical 401 response. Invalid input: 400. |
| R3 | THES-16 | GET /api/auth/me with valid session: 200 {id, display_name, email}; without session: 401 with error "Unauthorized". |
| R4 | THES-20 | POST /api/auth/logout: clear session cookie, return bodyless 204. No request body required; absent session remains successful. |
| R5 | THES-24, THES-186 | Authenticated display-name update persists 1–128 characters and appears in GET /api/auth/me. Missing session: 401; invalid length: 400. THES-186 proposes PATCH /api/auth/me returning 200 {id, display_name, email}; reuse THES-26 if already implemented. |
| R6 | THES-185 | DELETE /api/auth/me with valid session deletes account and memberships, clears session, returns bodyless 204. Missing session: 401. Project-owner blocking is an assumption below. |
| R7 | THES-2, THES-10 | Store passwords only as Argon2 hashes. Registration and login each allow 5 requests/minute/IP; excess requests return 429 with Retry-After. |
| R8 | THES-182 | Every non-2xx response uses {error: string, code: string}; omit code for generic framework errors. Domain codes are UPPER_SNAKE. Cover 400, 401, 404, 409, 422, 429, 503. |
| R9 | THES-184 | Cookies: SameSite=Lax, HttpOnly=true, Secure=true; explicit environment override permits local HTTP. Session carries account ID only. Reject non-JSON Content-Type on POST/PATCH/PUT/DELETE with 415; no GET changes state. Jira specifies no CSRF token. |

**Decisions still needed:**
- Exact password-strength rules and email validation/normalization are unspecified; confirm before implementation.
- Seven-day permanent session lifetime is a Jira assumption; signed-cookie versus server-side storage needs repository verification.
- THES-185 assumes 409 ACCOUNT_OWNS_PROJECTS while projects are owned; confirm before implementation. Transfer/delete projects belong to THES-55/THES-51.
- Reconcile R4 bodyless logout with R9 JSON-header enforcement; proposed resolution is a JSON Content-Type header with no body.
- R8 validation-detail representation and exact domain codes are unspecified.
