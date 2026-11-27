# Requirements — Assistant answer validation

- Ticket: `tickets/assistant-answer-validation.md`

## Requirements

| ID | Requirement | Source | Ticket lines | Scenarios |
| --- | --- | --- | --- | --- |
| R-001 | Present source-backed findings as verified only after validating relevance, factual claims and their cited passages. Withhold an off-topic draft. | from ticket | 13, 19, 25 | S-098, S-099 |
| R-002 | The review may narrow a claim or correct its citation. Display only the wording and passage supported by that review. | from ticket | 14, 20, 26 | S-100, S-101, S-109 |
| R-003 | Gather missing evidence before review when needed, within the original request limits. | from ticket | 14, 26 | S-102, S-103, S-113 |
| R-004 | Allow up to two evidence-recovery steps within the validation window. End generation after the review. | from ticket | 26, 33, 35 | S-102, S-103, S-113 |
| R-005 | At exhaustion, report supported findings and identify remaining evidence gaps. | from ticket | 15, 21 | S-103 |
| R-006 | While validation is pending, hide draft text. Show “Checking the answer against your sources…” only after five seconds. | from ticket | 27 | S-104 |
| R-007 | End validation and retries within 30 seconds of the first draft becoming ready. | from ticket | 33 | S-105, S-106 |
| R-008 | At the 30-second deadline, including a simultaneous service error, show verified findings with citations and identify unfinished checks. If nothing was verified and Gemini returned a draft before the deadline, offer “View unverified draft” only for claims still awaiting a check. Hide the draft until selected, label it unverified when opened, and exclude claims already found unsupported or off-topic. If no eligible text remains, say “I couldn’t verify an answer within 30 seconds. Please try again.” | from ticket | 34 | S-105, S-106, S-110, S-115, S-116 |
| R-009 | If the entire draft is off-topic, say “I couldn’t produce a verified answer to your question.” Describe a source gap only when the checked passages establish one. | from ticket | 28 | S-099, S-107 |
| R-010 | If a service error prevents validation before the deadline, withhold the draft and say “I couldn’t finish checking this answer. Please try again.” | from ticket | 29, 37 | S-108, S-114, S-120 |
| R-011 | Charge at most one draft attempt and one separate review attempt per Source Library exchange. Failure or timeout consumes its attempt. Disable automatic resends and count search embeddings separately. | from ticket | 35, 38 | S-111, S-112, S-113, S-114, S-115, S-119, S-120 |
| R-012 | Reuse only a fully reviewed success and its citations, with zero generation attempts, on an exact match of question, authorized project and conversation, selected sources, evidence, citation details, relevant context inputs and review configuration. Exclude partial answers, errors, timeouts and unverified drafts. | from ticket | 36 | S-111, S-117, S-118 |
| R-013 | On a fresh question with evidence, Gemini drafts once and separately reviews relevance and support against the question and cited passages. Check citation identities before display and withhold unsupported detail or attribution. | from ticket | 13, 20, 26, 38 | S-098, S-099, S-100, S-101, S-109, S-112, S-113 |
| R-014 | When an authorized search succeeds with no passages, explain that the search found insufficient evidence and use zero generation attempts. A failed initial search returns the interruption outcome without generation. | from ticket | 29, 37 | S-119, S-120 |

## Open Questions

- Should a writer be able to reopen the labeled draft in conversation history? The deadline decision covers the current exchange.

- Suggestion: requests without Source Library context (manuscript-only and general questions) keep their existing flow and are not validated, because the ticket covers source-backed answers only.
- Suggestion: progress delivery (D-006) streams records on the existing exchange request. Confirm it works with the production Gunicorn worker type and Flask-Limiter. If it does not, report progress by polling a status endpoint instead.
