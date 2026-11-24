# Repository findings for OpenAuth login

Theseus can reuse its Flask session and logout flow for provider sign-in. The main gap is account persistence. The identity model expects every user to have a password hash, and the repository can look up an account by ID or email but has no lookup by provider issuer and subject.

This source review maps the working tree to the [feature brief](brief.md) and [Gherkin scenarios](gherkin.feature) for issue #116. Google and Microsoft are scenario fixtures. Production provider selection remains open.

## Sign-in and callback

| Scenarios | Current behavior and implications |
|---|---|
| S-001–002 | The [sign-in page](../../../frontend/src/pages/signin.svelte) submits an email and password through the [auth client](../../../frontend/src/lib/api/auth.js). The [auth blueprint](../../../backend/domain/identity/api/auth/routes.py) exposes login, registration, current-user lookup and logout. It has no provider discovery, authorization redirect or callback handler. Provider buttons and the authorization request with PKCE, state, nonce and the specified scopes have no corresponding flow here. |
| S-008–009 | Password login returns user JSON and the page calls its success handler. A provider callback also needs to recover the originally requested local path and fall back to home for missing, invalid or external destinations, including scheme-relative URLs. |
| S-012–019 | The blueprint has no callback that verifies state, exchanges a code, validates the ID token or checks for an email with boolean `email_verified` set to true. The [user model](../../../backend/domain/identity/models/aggregates.py) has no suspension status to consult before starting a session. Consent denial, provider errors and exchange timeouts can be observed when Theseus receives a callback. If the browser never returns, S-017 checks the signed-out state when the user next opens Theseus. |

## Account selection and persistence

| Scenarios | Current behavior and implications |
|---|---|
| S-003–004, S-010–011 | The [repository contract](../../../backend/domain/identity/infrastructure/ports/identity_repository.py) exposes user insertion and lookups by ID and email. It has no operation to resolve an issuer and subject or create a user and identity link atomically. The returning-user scenarios depend on resolving that link first, including when the new provider email belongs to another account. |
| S-005 | The [email value object](../../../backend/domain/identity/models/value_objects.py) stores the validator's normalized address. The [PostgreSQL adapter](../../../backend/domain/identity/infrastructure/adapters/postgreqsql_identity_repository.py) compares email with SQL equality, and the [MongoDB adapter](../../../backend/domain/identity/infrastructure/adapters/mongodb_identity_repository.py) queries the stored email directly. Neither lookup explicitly compares the full address case-insensitively. S-005 exercises this distinction with a reloaded mixed-case password account whose credentials must survive the collision. |
| S-003, S-006–007 | The user model requires a password hash. PostgreSQL declares the column non-null, and both persistent adapters read and write a hash value. [Password login](../../../backend/domain/identity/services/auth/login_user.py) dereferences that value during verification. Credential-free provisioning therefore affects creation, reload and subsequent password login. The scenarios also specify a trimmed provider name of 1–50 characters or the fallback `Theseus user`. |

## Session, audit and verification

| Scenarios | Current behavior and implications |
|---|---|
| S-020–021 | The auth blueprint clears the session and stores the application user ID on successful password login. The [app factory](../../../backend/bootstrap/app.py) sets SameSite to Lax and enables Secure when `SESSION_COOKIE_SECURE=1`. Checking the callback's actual HTTPS response and inspecting browser-visible data and captured logs for provider tokens remain runtime verification work. |
| S-022–023 | Logout already clears the Flask session and returns HTTP 204. The existing login route has no explicit audit write. S-023 covers a successful provider login. The brief also calls for audit records for failed attempts observed by Theseus. |

The [identity service tests](../../../backend/tests/domain/identity/services/test_auth_integration.py) and [Playwright identity test](../../../e2e/identity.spec.js) are existing verification entry points. The browser test exercises password registration, sign-out, sign-in and session persistence after a page reload. That page reload does not exercise database serialization of an absent password hash. S-005 and S-007 specifically depend on reading a saved account back through a repository.
