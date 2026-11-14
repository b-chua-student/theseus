# Brief: Theseus Identity & Access Management
ID: THES-1
Owner: GLEN RAE RUIZ SUGUITAN
Date: 2026-11-14
Base SHA: 484154686ff1112417d014c308b5fef469127f98
Status: Scope approved by GLEN RAE RUIZ SUGUITAN on 2026-11-14; Q1–Q8 remain deferred.
## Goal
Enable users to establish and manage their identity and securely access Theseus through a session.
## Users / Roles
- New user, returning user, authenticated account holder.
## In Scope
- Register with display name, email and password; automatically sign in.
- Sign in, inspect the current account, and sign out.
- Update the current account's display name.
- Delete an account that owns no projects and remove its memberships.
- Authentication request limits, consistent errors, and session-cookie safeguards.
## Non-Goals
- Password reset, email verification, third-party sign-in, additional roles, or frontend redesign.
- Project transfer/deletion, other epic capabilities, and account deletion while projects are owned.
- Acceptance of unresolved proposals listed below; implementation, design and task generation.
## Constraints
- C1: Registration name/email/password and sign-in email/password have schema bounds of 1–128 characters; out-of-range input returns 400.
- C2: Duplicate registration returns 409 without a new account; approved password-strength failures return 422. Exact strength policy is deferred.
- C3: Registration returns 201; sign-in and session inspection return 200. Missing-session inspection, update and deletion return 401.
- C4: Each authentication operation allows at most five requests per minute per IP; throttled requests return 429 with Retry-After.
- C5: Non-success errors contain a string error; domain errors include a string UPPER_SNAKE code; generic framework errors omit code.
- C6: Session cookies use SameSite=Lax, HttpOnly and Secure; the local HTTP development override disables Secure. No CSRF token is required.
- C7: Nonempty non-JSON state-changing request bodies return 415. Reading information does not change application data.
- C8: Successful authenticated logout and eligible account deletion return 204 and clear the cookie. Logout requires no body; missing-session logout is safe.
- C9: A display name of 1–128 characters can be saved. Passwords are stored as Argon2 hashes, never plaintext.
## Known Touchpoints
Unverified Jira hints only: identity authentication/account services, auth routes and validation, session and limiter configuration, shared error handlers, account persistence and memberships. Do not explore code while authoring this brief.
## Assumptions
- Latest explicit Jira decisions override older examples only where unambiguous; proposals are not approvals.
- The whole epic is covered, including four unassigned supporting stories; this does not assign them to the owner.
- Existing scenario identifiers remain reserved; normalized tags and legacy aliases are documented in README.md.
## Open Questions
- Q1 Deferred: password policy (8–128/common-password rejection) awaits owner decision and a specified common-password list; exact strength examples excluded.
- Q2 Deferred: rate-limit bucket sharing, counting, reset/window and proxy IP rules need confirmation; only the five/minute/IP ceiling is accepted.
- Q3 Deferred: email format/case/normalization and exact duplicate error code/message are proposals; use the exact existing email for duplicate coverage.
- Q4 Deferred: cookie name/store and assumed seven-day lifetime/account-id-only payload need confirmation; excluded from acceptance.
- Q5 Deferred: exact update route, success body/status and invalid-name error status are proposed; retain only accepted update behavior.
- Q6 Deferred: JSON-only rules conflict with bodyless logout; exact missing-session logout status and required headers need approval. Bodyless logout acceptance scenarios are withheld.
- Q7 Deferred: deletion of project owners and ACCOUNT_OWNS_PROJECTS are assumptions; owned-project deletion excluded.
- Q8 Deferred: placement of structured validation details inside the new error envelope needs approval; only accepted envelope shape is covered.
- Q9 Resolved: Owner approved the scope; Base SHA records the commit inspected by Kiro.
## Success Criteria
1. Valid registration with a unique email creates one account, returns its id/name, and signs the user in; duplicate and out-of-range submissions fail without creating an account.
2. Valid credentials sign the user in and return their id/name; unknown email and incorrect password receive indistinguishable 401 errors without authentication.
3. A valid session reveals that account's id/name/email; no session returns 401 with error Unauthorized; inspection leaves application data unchanged.
4. Authenticated logout ends the browser session and clears its cookie; repeating logout without a session is safe. Body/header-specific assertions remain deferred.
5. An authenticated user can persist a display name of 1–128 characters and see it on subsequent inspection; unauthenticated updates fail without changes.
6. An authentication request beyond the five/minute/IP allowance is throttled with 429 and Retry-After; unrelated acceptance checks use unexhausted allowances.
7. Non-success responses follow C5, including 400/401/404/409/422/429/503 and 415; validation-detail placement is deferred.
8. Session-cookie flags match C6; otherwise valid JSON updates do not require a CSRF token; nonempty non-JSON state-changing bodies fail with 415.
9. Authenticated deletion of an account owning no projects removes the account and memberships, clears the cookie and returns 204; unauthenticated deletion changes nothing and returns 401.
10. Stored account passwords are Argon2 hashes and contain no persisted plaintext password; exact strength-policy checks await Q1.
## Reference Links
- Epic and review comments: https://theseus-inc.atlassian.net/browse/THES-1
- Registration: https://theseus-inc.atlassian.net/browse/THES-2
- Sign-in: https://theseus-inc.atlassian.net/browse/THES-10
- Session: https://theseus-inc.atlassian.net/browse/THES-16
- Logout: https://theseus-inc.atlassian.net/browse/THES-20
- Account update: https://theseus-inc.atlassian.net/browse/THES-24
- Shared errors: https://theseus-inc.atlassian.net/browse/THES-182
- Cookies: https://theseus-inc.atlassian.net/browse/THES-184
- Deletion: https://theseus-inc.atlassian.net/browse/THES-185
- Proposed update contract: https://theseus-inc.atlassian.net/browse/THES-186
