# Brief: OpenAuth login

- ID: openauth-login (#116)
- Owner: Unspecified in the ticket
- Date: 2026-11-25
- Base SHA: b4f5d2e

## Goal

Enable Theseus users to sign in with OpenAuth. (from ticket, line 5)

## Users / Roles

- Theseus users who want to sign in with OpenAuth. (from ticket, lines 1, 9)

## In Scope

- Sign in to Theseus through Google or Microsoft. (from ticket, line 13)
- Automatically create a passwordless account when a new identity signs in and its email matches no existing account. Start with the provider's display name and let the user edit it later. (from ticket, lines 40, 41)

- After sign-in, return users to the Theseus page they requested. Send them home if they started directly from sign-in or the requested page is unavailable. (from ticket, line 49)
- After an error, keep users signed out and show the sign-in page with a clear message, a “Try again” action, and guidance when their existing sign-in method is needed. (from ticket, line 50)
- When users return after an interruption, show “Sign-in wasn’t completed” and offer both a restart and another sign-in method. (from ticket, line 51)

## Non-Goals

- Changes to sign-in methods other than OpenAuth. (from ticket, line 30)
- Provider sign-out, new audit event types, and new retention rules. (from ticket, lines 55, 56)

## Constraints

- OpenAuth users end their Theseus session through the existing sign-out flow. Reuse existing sign-in audit events when available. (from ticket, lines 55, 56)
- Keep only the stable provider identity identifier, email, email verification status, and account display name. Discard tokens after authentication and omit raw profiles and unused fields from storage. (from ticket, lines 57, 58)

- A user must successfully authenticate with OpenAuth. Both providers support sign-in with an unverified email address. (from ticket, lines 13, 22)
- The ticket specifies no non-functional requirements. (from ticket, line 26)
- A linked identity still signs in to the same account after a provider email change. Only the usual email-change flow updates the Theseus email. (from ticket, line 34)
- If an unlinked identity matches an existing account by email, direct the user to their existing sign-in method. They can explicitly link the provider once signed in. (from ticket, line 35)
- Suspended accounts cannot sign in through OpenAuth. (from ticket, line 36)

## Known Touchpoints

- The Theseus sign-in experience. (from ticket, line 9)

## Assumptions

- No additional product decisions are assumed. The existing Gherkin illustrates proposals for the open questions below.

## Open Questions

- What initial display name should Theseus use if the provider supplies no usable name? “Theseus user” is a proposed fallback. (from ticket, line 45)
- Which performance, availability, accessibility, security, or privacy criteria should apply? Deferred: ticket line 26 sets no targets. One proposed target is a 95th-percentile sign-in callback time below 1.5 seconds excluding provider latency. Its measurement method remains open.

## Success Criteria

1. `@criterion-1` A Theseus user can start sign-in with OpenAuth. (from ticket, line 13)
2. `@criterion-2` A user who successfully signs in with OpenAuth is signed in to Theseus. (from ticket, line 17)
3. `@criterion-3` A user whose OpenAuth sign-in fails remains signed out of Theseus. (from ticket, lines 18, 22)

## Reference Links

- [Source ticket](../../../tickets/openauth-login.md)
- [GitHub issue #116](https://github.com/b-chua-student/theseus/issues/116)
