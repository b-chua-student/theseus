# Feature Intake: Email Login via OAuth

| Field | Value |
|---|---|
| **Feature name** | User can log in through email via OAuth |
| **Status** | Draft |
| **Requester** | _TBD_ |
| **Owner** | _TBD_ |
| **Priority** | _TBD_ |
| **Target release** | _TBD_ |

## 1. Summary

Allow a user to sign in to the application using the email identity held by a third-party OAuth 2.0 / OpenID Connect provider (e.g., Google, Microsoft), instead of creating and managing a separate password.

## 2. Problem Statement

Password-based sign-in adds friction (forgotten passwords, resets, weak credentials) and increases support load and security exposure. Users already have trusted email identities with major providers and expect one-click sign-in.

## 3. Goals

- Reduce sign-up and sign-in friction.
- Reduce password-reset support tickets.
- Rely on provider-verified emails to improve account trust.

## 4. Non-Goals

- Passwordless magic links or OTP by email.
- Account merging across different email addresses.
- Enterprise SSO / SAML.
- Provider-initiated logout (back-channel logout).

## 5. Proposed v1 decisions for human review

1. "Login through email via OAuth" means the user authenticates with an OAuth/OIDC provider and the app requires a verified provider email and recognizes linked identities by validated issuer and subject.
2. “OpenAuth” is the ticket name for this proposed OIDC sign-in flow. Enabled providers must supply the claims required by FR-4 and FR-5. Google and Microsoft are configured test fixtures in the Gherkin. Production provider selection and registration are deferred to deployment.
3. Authorization Code flow with **PKCE** is used; no implicit flow.
4. Sign-in with an unlinked identity and an unknown verified email creates a new account (just-in-time provisioning).
5. Defer linking additional identities to existing accounts. A verified email collision directs the user to their existing sign-in method.

## 6. Users and Personas

| Persona | Need |
|---|---|
| New visitor | Create an account quickly without a password |
| Returning user | Sign in with one click |
| Existing password user | Keep existing access and data when an unlinked identity has the same email |
| Support/Admin | Diagnose failed logins without seeing tokens |

## 7. Functional Requirements

| ID | Requirement |
|---|---|
| FR-1 | The login page shall display a "Continue with <Provider>" button per enabled provider. |
| FR-2 | Selecting a provider shall redirect the user to the provider's authorization endpoint using Authorization Code + PKCE, with `state` and `nonce`. |
| FR-3 | The app shall request only the `openid`, `email`, and `profile` scopes. |
| FR-4 | On callback, the app shall validate `state`, exchange the code for tokens, and validate the ID token (signature, issuer, audience, expiry, nonce). |
| FR-5 | The app shall only accept the email if `email_verified` is true. |
| FR-6 | After token and email validation, resolve the (issuer, subject) link first. An existing link selects its original account even if the email changed. Preserve stored emails and links. Create an account only if both the identity and case-insensitive email lookups find no match. Save the account and identity link atomically, with no password credential. Use the trimmed provider name when it contains 1–50 characters, otherwise use “Theseus user”. |
| FR-7 | When an unlinked identity matches any existing account email case-insensitively, leave the user signed out and direct them to their existing sign-in method. Preserve accounts and credentials. This applies regardless of stored verification history. |
| FR-8 | If the user denies consent or the provider returns an error, the app shall return the user to the login page with a clear message. |
| FR-9 | A session shall be established on success, and the user shall land on their originally requested local application path. Use the home page for missing, invalid, or external destinations, including scheme-relative URLs. |
| FR-10 | Disabled/suspended accounts shall be refused sign-in. |
| FR-11 | The user shall be able to log out, ending the app session. |
| FR-12 | All login attempts (success and failure) shall be written to an audit log. |

## 8. Non-Functional Requirements

- **Security:** Tokens never logged; session cookies are `HttpOnly`, `Secure`, `SameSite=Lax`; redirect URIs strictly allow-listed; CSRF protected via `state`.
- **Performance:** Callback processing p95 < 1.5 s excluding provider latency.
- **Availability:** Provider outage must not break other login methods.
- **Accessibility:** Buttons meet WCAG 2.1 AA; keyboard operable.
- **Privacy:** Store only email, name, avatar URL, provider issuer, and provider subject ID.
- **Compliance:** Consent and data handling aligned with applicable privacy law (GDPR / local equivalents).

## 9. User Flow (happy path)

1. User opens the login page and clicks "Continue with Google".
2. App redirects to the provider with PKCE challenge, `state`, `nonce`.
3. User authenticates and grants consent at the provider.
4. Provider redirects to the app callback with `code` and `state`.
5. App validates `state`, exchanges the code, validates the ID token.
6. App resolves the identity and applies FR-6 and FR-7 before creating a new account with its first identity link.
7. App creates a session and redirects the user to the app.

## 10. Edge Cases

- Email not verified by provider.
- Provider returns no email (user hid it or scope denied).
- Email changes at the provider after linking (match on validated issuer and `sub`, not email, after first link).
- Same email via two different providers.
- Expired or reused authorization code.
- Mismatched or missing `state`.
- User closes the provider window mid-flow.
- Email differs only by letter case.

## 11. Dependencies

- OAuth client registration with each provider (client ID/secret, redirect URIs).
- Secrets management for client secrets.
- A durable unique (issuer, subject) link, case-insensitive email uniqueness, and support for accounts without password credentials.
- Session management service.
- Audit logging service.

## 12. Risks

| Risk | Mitigation |
|---|---|
| Account takeover through unverified email | Require `email_verified`; refuse email-only linking under FR-7 and resolve existing links by issuer and subject |
| Provider outage | Keep alternate login methods; show friendly error |
| Redirect URI misconfiguration | Strict allow-list; environment-specific configs |
| Duplicate accounts | Case-insensitive email normalization and unique constraint |

## 13. Success Metrics

- % of logins completed via OAuth.
- Login success rate and drop-off at the consent step.
- Reduction in password-reset tickets.
- Time to first successful sign-in for new users.

## 14. Acceptance Criteria

Each scenario in `oauth-email-login.feature` has a stable ID and a criterion tag.

| Tag | Success criterion |
|---|---|
| @criterion-1 | Theseus offers configured providers and conducts the authorization flow without exposing provider tokens. |
| @criterion-2 | A validated, eligible identity establishes the intended Theseus session. Account selection, provisioning, redirect, auditing and logout follow FR-6 and FR-9 through FR-12. |
| @criterion-3 | Rejected, interrupted or incomplete authentication leaves the user signed out and preserves existing credentials. |

## 15. Deferred decisions

Production provider selection, additional account linking and unlinking, domain restrictions, additional MFA and remember-me behavior are deferred. Use the existing application session lifetime. The draft choices in section 5 are subject to human review for [issue #116](https://github.com/b-chua-student/theseus/issues/116).

## 16. Repository validation

| Scenario IDs | Review status | Repository implication |
|---|---|---|
| S-001–002 | Revised | Use configured provider fixtures. The current auth blueprint needs authorization and callback routes. |
| S-003–007 | Revised | The User aggregate requires a password hash, PostgreSQL requires a non-null hash, and MongoDB reads and writes a hash. Support an absent credential in the model and adapters while preserving password registration. The active LoginUser path must reject an absent credential with its normal invalid-credentials response. Exercise provisioning and collision checks after reload. |
| S-008–011 | Valid | Reuse the Flask user ID session. Local return-path validation and lookup by issuer and subject are implementation work. |
| S-012–015 | Valid | These outcomes require the new callback flow to reject unsuccessful attempts before issuing a session. |
| S-016–017 | Revised | A token-exchange timeout can produce an app error. An interrupted browser redirect is observable when the user returns. |
| S-018–019 | Valid | Add account-status enforcement and callback validation before issuing a session. |
| S-020–023 | Valid | Reuse session creation and logout. Enable secure cookies for HTTPS, protect provider tokens, and record application-observed login outcomes. |

Status describes review of the proposed behavior against the repository. Runtime acceptance remains part of implementation.
