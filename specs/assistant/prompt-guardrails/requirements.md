# Requirements — Assistant Prompt Guardrails and Safety Controls

- Ticket: `tickets/assistant-guardrails.md`

## Requirements

| ID | Requirement | Source | Ticket lines | Scenarios |
| --- | --- | --- | --- | --- |
| R-001 | By default, instruct the assistant to ground document claims honestly, refuse rule overrides, protect internal instructions, and ignore instructions embedded in manuscripts and retrieved excerpts. Apply fixed filters that block medium- and high-probability harassment, hate speech, sexually explicit content, and dangerous content. | from ticket | 10, 11, 12, 18, 19, 23, 32 | S-001, S-008 |
| R-002 | Allow general questions without attachments in none scope. The default instruction forbids claiming access to unattached manuscripts or sources. | from ticket | 7, 10, 15 | S-002 |
| R-003 | Keep retrieved excerpts inside explicit untrusted-data boundaries separate from the question, including when excerpts contain closing markers. | from ticket | 11, 12, 16 | S-003, S-006 |
| R-004 | Keep manuscript text inside explicit untrusted-data boundaries separate from the question, including when the manuscript contains closing markers. | from ticket | 11, 12, 17 | S-004, S-007 |
| R-005 | Verify default instructions, filter settings, document isolation, and ordinary answer delivery through automated checks without external credentials or network access. | from ticket | 20, 26 | S-005, S-009 |
| R-006 | Return answers to ordinary questions in none, manuscript, and source library scopes. | from ticket | 7, 15, 20 | S-009 |

## Open Questions

- None.
