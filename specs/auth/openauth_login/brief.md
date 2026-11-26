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

- Let returning users sign in with their previously approved Google account without repeated consent whenever Google permits it. (from ticket, line 88)

- Explain first-time account creation below the Google button, offer recovery specific to expiry or connectivity, and show the signed-in account’s Google connection status. (from ticket, lines 81–84)

- Sign in to Theseus through Google as the sole provider for sign-in and linking. (from ticket, line 13)
- Show the Google button on the regular sign-in page. An available provider starts sign-in. An unavailable provider shows an explanation on the same page. (from ticket, lines 76, 77)
- Automatically create a passwordless account when a new identity signs in and its email matches no existing account. Use the provider's display name when usable and “Theseus user” otherwise. The user can edit it later. (from ticket, lines 40, 41)

- After sign-in, return users to the Theseus page they requested. Send them home if they started directly from sign-in or the requested page is unavailable. (from ticket, line 49)
- After an error, keep users signed out and show the sign-in page with a clear message, a retry action appropriate to the failure, and guidance when their existing sign-in method is needed. (from ticket, lines 50, 82, 83)
- When users return after an interruption, show “Sign-in wasn’t completed” and offer both a restart and another sign-in method. (from ticket, line 51)

## Non-Goals

- Changes to sign-in methods other than OpenAuth. (from ticket, line 30)
- Provider sign-out, new audit event types, and new retention rules. (from ticket, lines 55, 56)

## Constraints

- OpenAuth users end their Theseus session through the existing sign-out flow. Reuse existing sign-in audit events when available. (from ticket, lines 55, 56)
- Keep only the stable provider identity identifier, email, email verification status, and account display name. Discard tokens after authentication and omit raw profiles and unused fields from storage. (from ticket, lines 57, 58)

- A user must successfully authenticate with OpenAuth. Google supports sign-in with an unverified email address. (from ticket, lines 13, 22)
- OpenAuth sign-in has no required performance target. (from ticket, line 26)
- A linked identity still signs in to the same account after a provider email change. Only the usual email-change flow updates the Theseus email. (from ticket, line 34)
- If an unlinked identity matches an existing account by email, direct the user to their existing sign-in method. They can explicitly link the provider once signed in. (from ticket, line 35)
- Suspended accounts cannot sign in through OpenAuth. (from ticket, line 36)

## Known Touchpoints

- The Theseus sign-in experience. (from ticket, line 9)

## Assumptions

- No additional product decisions are assumed.

## Open Questions

- Resolved. Use “Theseus user” when the provider supplies no usable display name. (from ticket, lines 41, 45)
- Resolved. No additional availability, accessibility, security, or privacy requirements apply to this release. (from ticket, line 26)

## Success Criteria

1. `@criterion-1` A Theseus user can start sign-in with OpenAuth. (from ticket, line 13)
2. `@criterion-2` A user who successfully signs in with OpenAuth is signed in to Theseus. (from ticket, line 17)
3. `@criterion-3` A user whose OpenAuth sign-in fails remains signed out of Theseus. (from ticket, lines 18, 22)
4. `@criterion-4` The Google button remains visible when Google is unavailable, and selecting it explains its status. (from ticket, lines 76, 77)

5. `@criterion-5` Users can see how Google registration works, restart expired requests, retry a connection failure, and check whether their account is linked. (from ticket, lines 81–84)

6. `@criterion-6` A returning user with reusable approval reaches Theseus without clicking Allow again. When Google requires interaction, the normal Google flow remains available. (from ticket, line 88)

## Reference Links

- [Source ticket](../../../tickets/openauth-login.md)
- [GitHub issue #116](https://github.com/b-chua-student/theseus/issues/116)
