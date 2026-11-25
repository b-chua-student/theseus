# Design — OpenAuth login

## Design

| ID | Decision | Components | Requirements |
| --- | --- | --- | --- |
| D-001 | Start sign-in on the server and bind the selected provider, state, nonce, PKCE verifier, expiry and validated local return path to a single-use pending request. | Flask auth blueprint, provider configuration, pending-request store | R-001, R-003 |
| D-002 | Exchange the code server-side and validate the provider response before resolving an account or establishing a session. | OIDC client, identity login service, Flask session | R-002, R-003 |
| D-003 | If provisioning is approved, commit the user and external identity atomically. Preserve legacy password users and resolve concurrent inserts using the committed identity. | Identity repository port, in-memory and persistent adapters, password login | R-002, R-003, R-004 |
| D-004 | Read authentication state from the existing session endpoint after navigation. If logout is included, confirm the server session ended before showing logout success. | App.svelte, signin.svelte, auth.js, Flask auth routes | R-001, R-002, R-003 |

## Components and Flow

The sign-in page fetches enabled providers and navigates to the selected start route. The route saves the pending request server-side, puts its opaque identifier in the browser session and redirects to the provider. The authorization request uses `response_type=code`, an S256 PKCE challenge, fresh state and nonce values, and the scopes `openid email profile`. Use atomic consumption and enforce expiry on read. A deployment with multiple workers needs a shared store.

The callback consumes the request, checks the provider binding and state, handles provider errors, exchanges the code with the saved verifier and verifies the ID token's signature, issuer, audience, expiry and nonce. Apply the approved email and account policies before setting the same user ID as password login in a freshly cleared Flask session. A rejected callback from a signed-out browser returns to sign-in without creating a session for a user. Redirect successful callbacks only to a validated application-local destination. Use `/settings/profile` as the non-home return-path fixture for S-008.

Under the proposed provisioning policy, first look up the issuer and subject. If a create loses **either** an identity or email uniqueness race, re-read that pair from committed storage after rolling back any failed transaction. If found, run the usual returning-user eligibility checks. Otherwise resolve the email owner and apply the approved collision policy. An unexpected storage error fails the attempt. A matching email alone never proves control of another identity.

## Data and Interfaces

- Proposed routes are `GET /api/auth/oauth/providers`, `GET /api/auth/oauth/<provider>/start` and the corresponding callback. Provider credentials, tokens and the verifier stay server-side. Use fixed failure codes and redact sensitive callback fields from logs.
- In MongoDB, embed external identities with an unambiguous key derived from the issuer and subject. Use a unique multikey index on `identities.key` with `partialFilterExpression: {"identities.key": {"$type": "string"}}`. Password-only users may omit identities. Backfill normalized email keys after a case-variant duplicate preflight, then enforce uniqueness for string email keys. Maintain that key on ordinary writes as well. Preserve existing IDs, emails and password hashes. A reloaded passwordless account follows the ordinary invalid-credentials path.
- If PostgreSQL is in scope, use one transaction for the user and identity inserts, a unique issuer/subject pair, normalized email uniqueness and a nullable password hash. Use the same repository contract for each approved adapter.
- Bootstrap the SPA from `GET /api/auth/me`. For logout, clear local user state and navigate to sign-in on `POST /api/auth/logout` returning 204. After an ambiguous failure, recheck `/me`. A 401 confirms logout. If the session is still active or cannot be checked, show a retryable failure and keep the UI from reporting success.

## Evidence Outcomes

A fresh browser can complete sign-in, reload, and obtain the same user from `/me`. Each rejected callback leaves a signed-out browser receiving 401. Exercise all examples in the reconciled Gherkin with a controlled provider.

Migrate at least two legacy MongoDB password users without identity keys, rerun the migration, register a third and verify password sign-in. Confirm duplicate external identities are rejected. Race two independent callbacks for the same new subject, including a forced email-conflict-first outcome. Both should resolve to one user and one link under the proposed policy. With different subjects sharing an email, assert the collision path preserves the original account.

For logout, exercise success, a request that never reaches Flask, and a lost response after Flask clears the session. Verify the resulting UI against the server session. Product choices and deployment scope are tracked in [Open Questions](requirements.md#open-questions).
