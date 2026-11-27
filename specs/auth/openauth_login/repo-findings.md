# Repository findings for OpenAuth login

Theseus can reuse the Flask user session, current-user endpoint and server logout endpoint. Two integration gaps affect the whole flow. The browser currently decides whether to show the signed-in UI from session storage, and the identity repository assumes that every account has a password. A successful provider callback must be visible to the browser after a full redirect, and a newly provisioned account must still be usable after a database reload.

This source review maps the working tree to the [feature brief](brief.md) and [Gherkin scenarios](gherkin.feature) for issue #116. The ticket specifies Google. The requirements and design record the approved account, recovery, session and data policies. The observations below describe the implementation baseline.

## Runtime wiring and browser navigation

| Integration point | Implementation consequence |
|---|---|
| Backend services | The [identity module](../../../backend/bootstrap/contexts/identity/module.py) wires password login and registration. The [container](../../../backend/bootstrap/container.py) supplies the repository and password hasher. Provider configuration and the identity-provider client need a wiring point here so callback tests can inject a controlled provider. The [dependency list](../../../backend/requirements.txt) includes OAuth libraries. The identity module currently wires no OIDC client. |
| Provider round trip | The [app factory](../../../backend/bootstrap/app.py) mounts the auth blueprint at `/api/auth`. For the draft flow, the design needs to specify how a pending request binds the initiating browser, provider, state, nonce, PKCE verifier and local return destination, when it expires, and how it is consumed. Keep token exchange and validation on the server. The draft requests exactly `openid email profile` and requires signature, issuer, audience, expiry and nonce validation before account lookup. |
| Signed-in UI | [App.svelte](../../../frontend/src/App.svelte) initializes its user from `getSession()`. The [auth client](../../../frontend/src/lib/api/auth.js) reads `theseus.session` from session storage, which password sign-in populates after a JSON response. A provider callback bypasses that JavaScript. On return, the UI can load the current user from `GET /api/auth/me` using the Flask cookie and handle a 401 as signed out. This avoids passing provider tokens or user details in the redirect URL. |
| Local destinations | Flask serves the SPA entry point for non-API frontend paths. App.svelte does not map those paths to views. Verify both the final URL and the rendered page for S-008. S-009 needs a home fallback for external destinations, including scheme-relative URLs. |
| Signing out | The browser's `signOut()` only removes the session-storage entry. The header handler then clears the Svelte user state. The existing backend `POST /api/auth/logout` clears the Flask session. S-022 needs the browser action to end the server session as well. A subsequent request to `/api/auth/me` can distinguish successful logout from a UI-only change. |

## Sign-in and callback

| Scenarios | Current behavior and implications |
|---|---|
| S-001–002 | The [sign-in page](../../../frontend/src/pages/signin.svelte) submits an email and password through the [auth client](../../../frontend/src/lib/api/auth.js). The [auth blueprint](../../../backend/domain/identity/api/auth/routes.py) exposes login, registration, current-user lookup and logout. It has no provider discovery, authorization redirect or callback handler. Provider buttons and the authorization request with PKCE, state, nonce and the specified scopes have no corresponding flow here. |
| S-008–009 | Password login returns user JSON and the page calls its success handler. A provider callback also needs to recover the originally requested local path and fall back to home for missing, invalid or external destinations, including scheme-relative URLs. |
| S-012–019 | The blueprint has no callback that verifies state, exchanges a code, validates the ID token or checks for the required email while accepting either verification status. The [user model](../../../backend/domain/identity/models/aggregates.py) has no suspension status to consult before starting a session. Consent denial, provider errors and exchange timeouts can be observed when Theseus receives a callback. If the browser never returns, S-017 checks the signed-out state when the user next opens Theseus. |

## Account selection and persistence

| Scenarios | Current behavior and implications |
|---|---|
| S-003–004, S-010–011 | The [repository contract](../../../backend/domain/identity/infrastructure/ports/identity_repository.py) exposes user insertion and lookups by ID and email. It has no operation to resolve an issuer and subject or create a user and identity link atomically. The returning-user scenarios depend on resolving that link first, including when the new provider email belongs to another account. |
| S-005 | The [email value object](../../../backend/domain/identity/models/value_objects.py) stores the validator's normalized address. The [PostgreSQL adapter](../../../backend/domain/identity/infrastructure/adapters/postgreqsql_identity_repository.py) compares email with SQL equality, and the [MongoDB adapter](../../../backend/domain/identity/infrastructure/adapters/mongodb_identity_repository.py) queries the stored email directly. Neither lookup explicitly compares the full address case-insensitively. S-005 exercises this distinction with a reloaded mixed-case password account whose credentials must survive the collision. |
| S-003, S-006–007 | The user model requires a password hash. PostgreSQL declares the column non-null, and both persistent adapters read and write a hash value. [Password login](../../../backend/domain/identity/services/auth/login_user.py) dereferences that value during verification. Credential-free provisioning therefore affects creation, reload and subsequent password login. The scenarios also specify a trimmed provider name of 1–50 characters or the fallback `Theseus user`. |

## Session, audit and verification

The default container uses the [in-memory identity adapter](../../../backend/domain/identity/infrastructure/adapters/in_memory_identity_repository.py). Outside tests, the app factory selects MongoDB when configured with `MONGODB_URI`. PostgreSQL has a separate adapter and is absent from that factory selection. In-memory results alone cannot establish compatibility with saved MongoDB documents or PostgreSQL rows.

For provisioning, use the same case-insensitive email comparison during lookup and uniqueness enforcement. Inspect existing data for addresses that differ only by case before introducing a unique comparison key. Existing password accounts must keep their IDs, stored addresses and working hashes. The PostgreSQL adapter uses autocommit and initializes with `CREATE TABLE IF NOT EXISTS`. Editing that declaration alone cannot update an existing table. The MongoDB adapter builds a unique index on the stored email and expects a password hash on every read.

Account creation and identity linking need one atomic repository operation under the provisioning policy. Two callbacks for the same new issuer and subject can both pass a preliminary lookup. Verify that they converge on one account and link. Two different subjects competing for one new email must preserve the winning account and send the other identity through the collision flow. An interrupted write must leave no orphan account or link.

| Scenarios | Current behavior and implications |
|---|---|
| S-020–021 | The auth blueprint clears the session and stores the application user ID on successful password login. The [app factory](../../../backend/bootstrap/app.py) sets SameSite to Lax and enables Secure when `SESSION_COOKIE_SECURE=1`. Checking the callback's actual HTTPS response and inspecting browser-visible data and captured logs for provider tokens remain runtime verification work. |
| S-022–023 | Logout already clears the Flask session and returns HTTP 204. The existing login route has no explicit audit write. S-023 covers a successful provider login. Failures follow the existing sign-in audit behavior. |

The [identity service tests](../../../backend/tests/domain/identity/services/test_auth_integration.py) and [Playwright identity test](../../../e2e/identity.spec.js) are existing verification entry points. The browser test exercises password registration, sign-out, sign-in and session persistence after a page reload. That page reload does not exercise database serialization of an absent password hash. S-005 and S-007 specifically depend on reading a saved account back through a repository.

| Verification layer | Evidence to collect from the approved scenarios |
|---|---|
| Flask callback | Use a controlled provider for success, denial, timeout and the individual invalid-callback examples in S-019. On rejection, check the user-facing outcome, signed-out response from `/me`, and absence of unintended account or link writes. For S-017, reopen the app without delivering any callback. |
| Identity storage | Round-trip a legacy password account and an OAuth-only account through each persistent adapter in scope. Exercise email collisions, changed provider emails, name fallback, password rejection, concurrent provisioning and interrupted writes. Keep the existing password sign-in test as a regression check. |
| Browser and session | Start with empty session storage, finish a provider redirect, reload the destination, then sign out and request a protected resource. Inspect the actual HTTPS session cookie for HttpOnly, Secure and SameSite=Lax. Check browser storage, redirect URLs and captured logs for provider token exposure. |
| Audit | Compare success and rejection with existing sign-in audit behavior. Reuse events where present and check that logged fields exclude tokens. |

This review records static source evidence. After intake and Gherkin approval, the repository workflow calls for traceable requirements, design and tasks, followed by executable scenario tests run before application changes.
