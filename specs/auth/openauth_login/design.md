# Design — OpenAuth login

## Design

| ID | Decision | Components | Requirements |
| --- | --- | --- | --- |
| D-001 | Start sign-in on the server and bind the selected provider, state, nonce, PKCE verifier, expiry and validated local return path to a single-use pending request. | Flask auth blueprint, provider configuration, pending-request store | R-001, R-003 |
| D-002 | Exchange the code server-side and validate the provider response before resolving an account or establishing a session. | OIDC client, identity login service, Flask session | R-002, R-003 |
| D-003 | Commit the user and external identity atomically. Preserve legacy password users and resolve concurrent inserts using the committed identity. | Identity repository port, in-memory and persistent adapters, password login | R-002, R-003, R-004 |
| D-004 | Read authentication state from the existing session endpoint after navigation. Confirm the server session ended before showing logout success. | App.svelte, signin.svelte, auth.js, Flask auth routes | R-001, R-002, R-003 |
| D-005 | The signed-in user selects Link provider and submits a CSRF-protected POST to `/api/auth/oauth/<provider>/link`. Bind the single-use authorization request to the link action, session, and account. On a validated callback in the same authenticated session, atomically attach the issuer and subject to that account. Reject an identity owned by another account without changing either account. | Account UI, Flask auth blueprint, pending-request store, identity repository | R-005 |
| D-006 | Resolve linked identities before email lookup and preserve their account email. Check suspension before granting a session. On an unmatched email create a passwordless account with the usable provider name or “Theseus user”. Trim the provider name and accept 1–50 characters. Save later edits on the Theseus profile and preserve them on subsequent sign-ins. | Identity service, user aggregate, repository adapters, profile editor | R-006, R-007, R-008, R-009, R-010 |
| D-007 | Restore the requested local view or home. Map failures to a sign-in message and retry action, including existing-method guidance on collision. On return from an unfinished attempt show the interruption message and restart and alternate-method controls. | Sign-in page, SPA navigation, pending request store | R-005, R-011, R-012, R-013 |
| D-008 | End the Theseus session through existing logout. Reuse the ordinary sign-in audit hook if present. Allowlist account claims on persistence, discard tokens on every exit and redact them from logs and browser responses. | Session routes, provider client, identity adapters, sign-in audit integration | R-014, R-015, R-016, R-017 |
| D-009 | Render only the Google choice above the password form. Use server settings to start configured providers and report unavailable choices inline. | Sign-in page | R-018 |
| D-010 | Add registration guidance under the Google control and map expired attempts and provider connection failures to distinct notices and actions. | Sign-in page, OAuth callback | R-019, R-020 |
| D-011 | Read the current account’s persisted identity for the Google issuer when Account opens and return its connection status. | Identity repository adapters, provider settings endpoint, account menu | R-021 |
| D-012 | Remember the last verified Google subject as a browser account hint across Theseus logout. On explicit sign-in request silent authorization for that subject, with a fresh interactive attempt if Google requires it. Allow switching accounts. Verify every callback before creating a session. | OAuth routes, sign-in page, browser session | R-022 |

## Components and Flow

The sign-in page fetches enabled providers and navigates to the selected start route. The route saves the pending request server-side, puts its opaque identifier in the browser session and redirects to the provider. The authorization request uses `response_type=code`, an S256 PKCE challenge, fresh state and nonce values, and the scopes `openid email profile`. Use atomic consumption and enforce expiry on read. A deployment with multiple workers needs a shared store.

The callback consumes the request, checks the provider binding and state, handles provider errors, exchanges the code with the saved verifier and verifies the ID token's signature, issuer, audience, expiry and nonce. Require an email and accept either verification status. Reject suspended accounts before setting the same user ID as password login in a freshly cleared Flask session. A rejected callback from a signed-out browser returns to sign-in without creating a session for a user. Redirect successful callbacks only to a validated application-local destination. For S-008 restore an existing protected view and verify its rendered content. Fall back to home for an unavailable view.

On return without a callback, use the initiating browser's pending-attempt marker to show the interruption message. A restart creates a fresh request. Clear the marker on terminal success or failure so an ordinary visit does not show a stale warning.

First look up the issuer and subject. If a create loses **either** an identity or email uniqueness race, re-read that pair from committed storage after rolling back any failed transaction. If found, run the usual returning-user eligibility checks. Otherwise resolve the email owner and apply the approved collision policy. An unexpected storage error fails the attempt. A matching email alone never proves control of another identity.

## Data and Interfaces

- Proposed routes are `GET /api/auth/oauth/providers`, `GET /api/auth/oauth/<provider>/start` and the corresponding callback. Provider credentials, tokens and the verifier stay server-side. Use fixed failure codes and redact sensitive callback fields from logs.
- In MongoDB, embed external identities with an unambiguous key derived from the issuer and subject. Use a unique multikey index on `identities.key` with `partialFilterExpression: {"identities.key": {"$type": "string"}}`. Password-only users may omit identities. Backfill normalized email keys after a case-variant duplicate preflight, then enforce uniqueness for string email keys. Maintain that key on ordinary writes as well. Preserve existing IDs, emails and password hashes. A reloaded passwordless account follows the ordinary invalid-credentials path.
- For the existing PostgreSQL adapter, use one transaction for the user and identity inserts, a unique issuer/subject pair, normalized email uniqueness and a nullable password hash. Use the same repository contract for all three existing adapters.
- Bootstrap the SPA from `GET /api/auth/me`. For logout, clear local user state and navigate to sign-in on `POST /api/auth/logout` returning 204. After an ambiguous failure, recheck `/me`. A 401 confirms logout. If the session is still active or cannot be checked, show a retryable failure and keep the UI from reporting success.

## Evidence Outcomes

A fresh browser can complete sign-in, reload, and obtain the same user from `/me`. Each rejected callback leaves a signed-out browser receiving 401. Use a controlled provider. For S-019 exercise missing and mismatched state, expired and replayed authorization codes, and ID tokens with invalid signature, issuer, audience, expiry or nonce. For S-021 inspect the HTTPS session cookie for HttpOnly, Secure and SameSite=Lax alongside the protected-page check.

Migrate at least two legacy MongoDB password users without identity keys, rerun the migration, register a third and verify password sign-in. Confirm duplicate external identities are rejected. Race two independent callbacks for the same new subject, including a forced email-conflict-first outcome. Both should resolve to one user and one link. With different subjects sharing an email, assert the collision path preserves the original account.

For logout, exercise success, a request that never reaches Flask, and a lost response after Flask clears the session. Verify the resulting UI against the server session.
