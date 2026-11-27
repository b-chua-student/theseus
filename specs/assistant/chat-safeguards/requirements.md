# Requirements — Assistant chat safeguards

- Ticket: `tickets/assistant-safeguards.md`

## Requirements

| ID | Requirement | Source | Ticket lines | Scenarios |
| --- | --- | --- | --- | --- |
| R-001 | Reject direct attempts to override or disclose internal instructions with a prompt-injection error before calling the model. Preserve every prior exchange and leave no pending or stored exchange for the rejected question. | from ticket | 10, 14 | S-010, S-011, S-016 |
| R-002 | Forward benign academic questions about prompt injection or system prompts to the model and return its answer to the writer. | from ticket | 15 | S-015 |
| R-003 | With the default burst limit enabled and no recent submissions, accept the first ten ordinary questions from one client within a minute. Reject the eleventh with a rate-limit error before calling the model for it. | from ticket | 16, 21 | S-012 |
| R-004 | In automated runs using default test settings, accept the same eleven questions without rate-limit rejection. Allow tests to enable limiting explicitly. | from ticket | 17 | S-018, S-012 |
| R-005 | By default, forward the most recent ten completed exchanges, or all completed exchanges if fewer exist, in chronological order. Preserve all prior exchanges in storage. | from ticket | 18, 21 | S-013, S-017 |
| R-006 | Verify rejection, benign pass-through, rate limiting, and history capping without network access or live credentials. | from ticket | 24 | S-014 |

## Open Questions

- None.
