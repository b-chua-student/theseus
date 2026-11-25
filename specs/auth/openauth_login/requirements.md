# Requirements — OpenAuth login

- Ticket: `tickets/openauth-login.md`

## Requirements

| ID | Requirement | Source | Ticket lines | Scenarios |
| --- | --- | --- | --- | --- |
| R-001 | A Theseus user can choose Google or Microsoft to start OpenAuth sign-in. | from ticket | 5, 13 | S-001, S-002 |
| R-002 | Successful OpenAuth sign-in establishes a Theseus session. | from ticket | 17 | S-003, S-004, S-006, S-008, S-009, S-010, S-011, S-012, S-021, S-024 |
| R-003 | Completing OpenAuth sign-in requires successful OpenAuth authentication. A failed attempt leaves the user signed out. | from ticket | 18, 22 | S-005, S-013, S-014, S-015, S-016, S-017, S-018, S-019 |
| R-004 | Other sign-in methods retain their existing behavior. | from ticket | 30 | S-005, S-007 |
| R-005 | On an unlinked email match, direct the user to their existing sign-in method. Once authenticated, they can explicitly link the provider for future sign-in. | from ticket | 35 | S-005, S-024 |
| R-006 | Theseus accepts a successfully authenticated Google or Microsoft user whose provider email is unverified. | from ticket | 13, 22 | S-012 |
| R-007 | A linked identity selects its existing account even after a provider email change. The Theseus email changes only through the usual email-change flow. | from ticket | 34 | S-004, S-010, S-011 |
| R-008 | Suspended accounts cannot sign in through OpenAuth. | from ticket | 36 | S-018 |
| R-009 | For a new identity with an unmatched email, create a passwordless account automatically. | from ticket | 40 | S-003, S-006, S-007, S-012 |
| R-010 | Initialize the editable display name from the provider, using “Theseus user” if no usable name is supplied. | from ticket | 41 | S-003, S-006, S-025 |
| R-011 | Return users to the Theseus page they requested, or home for direct sign-in or an unavailable destination. | from ticket | 49 | S-003, S-004, S-008, S-009, S-026 |
| R-012 | On error, return signed-out users to sign-in with a clear message and “Try again”. Explain the existing method when needed. | from ticket | 50 | S-005, S-013, S-014, S-015, S-016, S-018, S-019 |
| R-013 | After interruption, show “Sign-in wasn’t completed” on return and offer restart or another sign-in method. | from ticket | 51 | S-017 |
| R-014 | The existing Theseus sign-out flow ends the Theseus session. | from ticket | 55 | S-022 |
| R-015 | Reuse existing sign-in audit events when available. | from ticket | 56 | S-015, S-019, S-023 |
| R-016 | Retain only the stable provider identifier and the email, email verification status and display name needed for the account. | from ticket | 57, 58 | S-027 |
| R-017 | Use provider tokens only during authentication and discard them afterward. Omit raw profiles and unused fields from storage. | from ticket | 58 | S-020, S-023, S-027, S-028 |
| R-018 | Show both provider buttons on the regular sign-in page. Start available providers and explain unavailable choices on the same page. | from ticket | 76, 77 | S-002, S-029 |

## Open Questions

None outstanding in the ticket.
