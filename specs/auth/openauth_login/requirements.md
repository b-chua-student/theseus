# Requirements — OpenAuth login

- Ticket: `tickets/openauth-login.md`

## Requirements

| ID | Requirement | Source | Ticket lines | Scenarios |
| --- | --- | --- | --- | --- |
| R-001 | A Theseus user can initiate OpenAuth sign-in. | from ticket | 5, 13 | S-001, S-002 |
| R-002 | Successful OpenAuth sign-in establishes a Theseus session. | from ticket | 17 | S-003, S-004, S-006, S-008, S-009, S-010, S-011 |
| R-003 | Completing OpenAuth sign-in requires successful OpenAuth authentication. A failed attempt leaves the user signed out. | from ticket | 18, 22 | S-005, S-012, S-013, S-014, S-015, S-016, S-017, S-018, S-019 |
| R-004 | Other sign-in methods retain their existing behavior. | from ticket | 30 | S-005, S-007 |

## Open Questions

The ticket leaves provider selection and existing-account policy open on lines 34–35. The current Gherkin illustrates specific answers. Before implementation, record the approved answers in the ticket, reconcile the brief and Gherkin, and update these drafts. Scenario references identify related examples, not approval of every detail.

- Which providers can be enabled, and what evidence of email verification qualifies each one? Google and Microsoft appear in the test examples.
- Should a verified new identity create a passwordless account? Confirm the display-name fallback, subject-based matching when emails change, refusal to link by email alone, and how suspension affects the outcome.
- Confirm the intended destination and user-facing error messages, including interrupted sign-in. S-008 uses a path the SPA does not currently render as a dedicated page.
- Are logout, audit events and their fields, token exposure checks, and production cookie attributes in scope as specified in S-015 and S-020 through S-023?
- Which storage adapters and deployment configurations must support the feature? Confirm PostgreSQL scope and where pending requests live across workers.
- Ticket line 26 specifies no non-functional targets. Should latency or accessibility checks become acceptance criteria? The previously suggested 1.5-second p95 threshold would need an agreed measurement method.
