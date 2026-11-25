# Requirements — Assistant answer validation

- Ticket: `tickets/assistant-answer-validation.md`

## Requirements

| ID | Requirement | Source | Ticket lines | Scenarios |
| --- | --- | --- | --- | --- |
| R-001 | Display a source-backed draft only after validating relevance, factual claims and their cited passages. Withhold an off-topic draft. | from ticket | 13, 19, 25 | S-001, S-002 |
| R-002 | Revise overstatements and incorrect citations and check the replacement before display. | from ticket | 14, 20 | S-003, S-004 |
| R-003 | When passages are insufficient and a retry remains, search for better evidence and check the resulting draft. | from ticket | 14, 20 | S-005 |
| R-004 | Allow at most two retries after initial validation, shared across revision and retrieval. A combined revision and search with its check consumes one retry. | from ticket | 26 | S-006, S-010 |
| R-005 | At exhaustion, report supported findings and identify remaining evidence gaps. | from ticket | 15, 21 | S-006 |
| R-006 | While validation is pending, hide draft text. Show “Checking the answer against your sources…” only after five seconds. | from ticket | 27 | S-007 |
| R-007 | End validation and retries within 30 seconds of the first draft becoming ready. | from ticket | 33 | S-008, S-009 |
| R-008 | At the deadline, return validated findings and remaining gaps. If no validation completed, tell the user the answer could not be checked. | from ticket | 34 | S-008, S-009 |
| R-009 | If every draft is off-topic at exhaustion, say “I couldn’t produce a verified answer to your question.” Report a source gap only if checked evidence establishes it. | from ticket | 28 | S-010 |
| R-010 | If a service error prevents validation, withhold the draft and say “I couldn’t finish checking this answer. Please try again.” | from ticket | 29 | S-011 |

## Open Questions

None for source-backed answer validation. The suggestions below are not requirements.

- Suggestion: requests without Source Library context (manuscript-only and general questions) keep their existing flow and are not validated, because the ticket covers source-backed answers only.
- Suggestion: progress delivery (D-006) streams records on the existing exchange request. Confirm it works with the production Gunicorn worker type and Flask-Limiter. If it does not, report progress by polling a status endpoint instead.
