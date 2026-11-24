# Feature Intake: Email Login via OAuth

## Goal

Allow a user to sign in to the application using the email identity held by a third-party OAuth 2.0 / OpenID Connect provider (e.g., Google, Microsoft), instead of creating and managing a separate password.

- Reduce sign-up and sign-in friction.
- Reduce password-reset support tickets.
- Rely on provider-verified emails to improve account trust.

## Non-Goals

- Passwordless magic links or OTP by email.
- Account merging across different email addresses.
- Enterprise SSO / SAML.
- Provider-initiated logout (back-channel logout).

## In Scope

1. "Login through email via OAuth" means the user authenticates with an OAuth/OIDC provider and the app requires a verified provider email and recognizes linked identities by validated issuer and subject.
2. “OpenAuth” is the ticket name for this proposed OIDC sign-in flow. Enabled providers must supply the claims required by FR-4 and FR-5. Google and Microsoft are configured test fixtures in the Gherkin. Production provider selection and registration are deferred to deployment.
3. Authorization Code flow with **PKCE** is used; no implicit flow.
4. Sign-in with an unlinked identity and an unknown verified email creates a new account (just-in-time provisioning).
5. Defer linking additional identities to existing accounts. A verified email collision directs the user to their existing sign-in method.

### Functional Requirements

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

## Constraints

- **Security:** Tokens never logged; session cookies are `HttpOnly`, `Secure`, `SameSite=Lax`; redirect URIs strictly allow-listed; CSRF protected via `state`.
- **Performance:** Callback processing p95 < 1.5 s excluding provider latency.
- **Availability:** Provider outage must not break other login methods.
- **Accessibility:** Buttons meet WCAG 2.1 AA; keyboard operable.
- **Privacy:** Store only email, name, avatar URL, provider issuer, and provider subject ID.
- **Compliance:** Consent and data handling aligned with applicable privacy law (GDPR / local equivalents).

## Success Criteria

Each scenario in `gherkin.feature` has a stable ID and a criterion tag.

| Tag | Success criterion |
|---|---|
| @criterion-1 | Theseus offers configured providers and conducts the authorization flow without exposing provider tokens. |
| @criterion-2 | A validated, eligible identity establishes the intended Theseus session. Account selection, provisioning, redirect, auditing and logout follow FR-6 and FR-9 through FR-12. |
| @criterion-3 | Rejected, interrupted or incomplete authentication leaves the user signed out and preserves existing credentials. |

## Deferred decisions

Production provider selection, additional account linking and unlinking, domain restrictions, additional MFA and remember-me behavior are deferred. Use the existing application session lifetime. The draft choices in the In Scope section are subject to human review for [issue #116](https://github.com/b-chua-student/theseus/issues/116).

## Repository validation

| Scenario IDs | Review status | Repository implication |
|---|---|---|
| S-001–002 | Revised (assumed) | The login page offers each enabled provider. Selecting one redirects the user to that provider with the authorization parameters and scopes in FR-2 and FR-3. |
| S-003–007 | Revised (assumed) | A new identity with a new verified email signs in to a linked account created without a password credential, with the display name specified in FR-6. A returning linked identity signs in to the same account. After reload, password login for the OAuth-only account returns the ordinary invalid-credentials response and leaves the user signed out. An unlinked identity matching a reloaded account’s email case-insensitively also stays signed out, is directed to the existing sign-in method, and leaves the account and credentials unchanged, without creating a link or duplicate. |
| S-008–011 | Valid | Reuse the Flask user ID session. Local return-path validation and lookup by issuer and subject are implementation work. |
| S-012–015 | Valid | These outcomes require the new callback flow to reject unsuccessful attempts before issuing a session. |
| S-016–017 | Revised | A token-exchange timeout can produce an app error. An interrupted browser redirect is observable when the user returns. |
| S-018–019 | Valid | Add account-status enforcement and callback validation before issuing a session. |
| S-020–023 | Valid | Reuse session creation and logout. Enable secure cookies for HTTPS, protect provider tokens, and record application-observed login outcomes. |

Status describes review of the proposed behavior against the repository. Runtime acceptance remains part of implementation.
