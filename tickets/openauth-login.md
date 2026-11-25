# [openauth-login] As a Theseus user, I can sign in with OpenAuth

## Intent

Let Theseus users sign in with OpenAuth.

## Context

This ticket covers the sign-in experience for Theseus users.

## Scope

- Sign in to Theseus with OpenAuth through Google or Microsoft.

## Expected Outcomes

- [ ] A user who successfully signs in with OpenAuth is signed in to Theseus.
- [ ] A user who fails to sign in with OpenAuth remains signed out of Theseus.

## Rules / Constraints

- Theseus requires successful OpenAuth authentication. Users can sign in even if their provider has not verified their email address.

## Non-Functional Requirements

The SDD workflow does not require a performance target. None is specified for OpenAuth sign-in.

## Out of Scope

- Changes to sign-in methods other than OpenAuth.

## Existing accounts

- A linked identity continues to identify the same account when the provider email changes. The Theseus email stays unchanged until the user updates it through the usual email-change flow.
- If an unlinked identity's email matches an existing account, direct the user to their existing sign-in method. Once signed in, the user can explicitly link the provider.
- Deny OpenAuth sign-in to suspended accounts.

## New accounts

- On successful sign-in with a new identity whose email matches no existing account, Theseus automatically creates a passwordless account.
- Use the provider's display name as the initial Theseus display name. The user can edit it later.

## Open Questions

- What initial display name should Theseus use if the provider supplies no usable name?

## Sign-in destinations and recovery

- After sign-in, return the user to the Theseus page they tried to open. Use the home page if they started directly from sign-in or the original page is unavailable.
- On a sign-in error, keep the user signed out and return them to the sign-in page with a clear message and a “Try again” action. If they need their existing sign-in method, explain how to continue with it.
- When a user returns to Theseus after an interrupted sign-in, show “Sign-in wasn’t completed” and let them restart or choose another sign-in method.

## Session, auditing, and provider data

- OpenAuth users can end their Theseus session through the existing Theseus sign-out flow. Signing out of Google or Microsoft is outside this feature's scope.
- Use the same sign-in audit events as other Theseus sign-in methods if those events already exist. Defer new event types and retention rules.
- Retain only the provider's stable identity identifier for future sign-ins and the email, email verification status, and display name needed for the Theseus account.
- Use provider tokens only during authentication and discard them afterward. Do not store raw provider profiles or unused fields.

## Output Paths

- Intake brief: `specs/auth/openauth_login/brief.md`
- Gherkin: `specs/auth/openauth_login/gherkin.feature`
- Spec files: `requirements.md`, `design.md`, and `tasks.md` in `specs/auth/openauth_login/`.

## Definition of Done

- [ ] Intake generated and approved
- [ ] Gherkin generated and approved
- [ ] Open questions resolved
- [ ] Spec, Gherkin, and code in sync
- [ ] Reviewed and merged
