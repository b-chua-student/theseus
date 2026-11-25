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

## Non-Goals

- Changes to sign-in methods other than OpenAuth. (from ticket, line 30)

## Constraints

- A user must successfully authenticate with OpenAuth. Both providers support sign-in with an unverified email address. (from ticket, lines 13, 22)
- The ticket specifies no non-functional requirements. (from ticket, line 26)

## Known Touchpoints

- The Theseus sign-in experience. (from ticket, line 9)

## Assumptions

- No additional product decisions are assumed. The existing Gherkin illustrates proposals for the open questions below.

## Open Questions

- How should existing accounts be handled? Ticket line 34 leaves account matching open. One proposal is to recognize a previously linked identity even after an email change, direct an unlinked user with a matching email to their existing sign-in method, and refuse sign-in to suspended accounts.
- Should a new identity create a passwordless account automatically, and what display name should it receive? Deferred: the ticket does not define provisioning or a fallback name.
- Where should users land after sign-in, and what should they see after an error or interruption? Deferred: ticket lines 17 and 18 specify sign-in status only.
- Should this feature include logout, audit events, or limits on stored profile data? Deferred: the ticket does not specify these behaviors.
- Which performance, availability, accessibility, security, or privacy criteria should apply? Deferred: ticket line 26 sets no targets. One proposed target is a 95th-percentile sign-in callback time below 1.5 seconds excluding provider latency. Its measurement method remains open.

## Success Criteria

1. `@criterion-1` A Theseus user can start sign-in with OpenAuth. (from ticket, line 13)
2. `@criterion-2` A user who successfully signs in with OpenAuth is signed in to Theseus. (from ticket, line 17)
3. `@criterion-3` A user whose OpenAuth sign-in fails remains signed out of Theseus. (from ticket, lines 18, 22)

## Reference Links

- [Source ticket](../../../tickets/openauth-login.md)
- [GitHub issue #116](https://github.com/b-chua-student/theseus/issues/116)
