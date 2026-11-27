# Design

## Decisions

| ID | Decision | Affected components | Requirements |
| --- | --- | --- | --- |
| D-001 | Supply the instruction specified in requirements.md and set BLOCK_MEDIUM_AND_ABOVE for HARM_CATEGORY_HARASSMENT, HARM_CATEGORY_HATE_SPEECH, HARM_CATEGORY_SEXUALLY_EXPLICIT, and HARM_CATEGORY_DANGEROUS_CONTENT when constructing the default Gemini request configuration. Preserve explicitly supplied instructions. Inspect the configuration passed to the provider on reply so the check covers application defaults through request dispatch. | Application bootstrap, Gemini adapter | R-001, R-002 |
| D-002 | Keep source formatting in the adapter. Encode reserved boundary text in every interpolated reference field before enclosing the numbered excerpts and locations. Append the original question after the closing boundary. Preserve the existing plain-question path when retrieval yields no excerpts. | Gemini adapter | R-002, R-003 |
| D-003 | Apply the same boundary encoding convention to trimmed manuscript text at the service's existing assembly point. Retain its reference instruction and empty placeholder. Pass the writer's original question after the block. | Chat service | R-004 |
| D-004 | Substitute the provider client at construction, supply a dummy credential, and disable external network access for verification. Capture the actual outgoing configuration and final message at the provider call. | Gemini adapter tests, offline test setup | R-001, R-002, R-003, R-004, R-005 |
| D-005 | Exercise the normal service entry point with a controlled reply for each scope. Inspect the returned answer and saved exchange. Preserve scope routing, retrieval fallback, and conversation history. | Chat service, service tests | R-002, R-006 |

## Verification boundaries

Request inspection establishes which controls the application sends. A controlled reply establishes answer delivery. Neither observation measures a live provider's refusal behavior or filtering effectiveness.
