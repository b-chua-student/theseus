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

None specified.

## Out of Scope

- Changes to sign-in methods other than OpenAuth.

## Open Questions

- How should OpenAuth sign-in handle users with existing Theseus accounts?

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
