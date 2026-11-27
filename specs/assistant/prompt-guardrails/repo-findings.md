# Repository findings for assistant prompt guardrails

Reviewed the working tree at HEAD `3a29549` against the [proposed ticket](../../../tickets/assistant-guardrails.md) and [Gherkin scenarios](gherkin.feature). These findings describe the current code and test assertions. No tests or external model calls were run.

| Scenarios | Current behavior | Verification gap |
| --- | --- | --- |
| S-001, S-008 | Bootstrap constructs the Gemini adapter without overrides. Its system instruction defaults to `None`. The request configuration supplies no explicit safety settings. | Check the configuration actually sent with a request for the expected instructions and filter settings. Provider-side defaults cannot be established from this code. |
| S-002 | In none scope the service skips retrieval. With no retrieved context, the adapter sends the question as supplied. Previous conversation turns are still included. | The existing service test checks the plain question and empty context. It does not establish what the default instruction says about general questions or access to unattached documents. |
| S-003, S-006 | The Gemini adapter formats each retrieved excerpt with its location and text, then appends the question. The source list has a heading but no explicit closing boundary. | The service tests observe retrieved chunks before final formatting. Check containment and separation in the outgoing message, including when an excerpt contains boundary-like text. |
| S-004, S-007 | The service labels manuscript text as reference material and appends the question. It interpolates the trimmed manuscript directly and substitutes a placeholder for an empty manuscript. | Existing tests cover ordinary and empty manuscripts. Check explicit containment in the assembled message when manuscript text contains boundary-like text. |
| S-005 | Service tests substitute a chat model. The concrete adapter loads environment settings, requires a key at construction, and calls the Gemini client on reply. | Exercise the concrete configuration and formatting with a substituted provider client and dummy key. Verify the suite succeeds with external network access unavailable. |
| S-009 | All three scopes reach the same reply path. On success the service records the answer, saves the conversation, and returns the answer. | Existing tests cover answer delivery and scope routing separately. Exercise the three ordinary-question examples with controlled replies and assert the returned answers. |

## Code and test evidence

- [Application bootstrap](../../../backend/bootstrap/app.py) constructs the default adapter in the application path.
- [Gemini adapter](../../../backend/domain/assistant/infrastructure/adapters/gemini_chat_model.py) owns request configuration, history formatting, source formatting, and the provider call.
- [Chat service](../../../backend/domain/assistant/services/chat.py) owns scope selection, optional retrieval, manuscript formatting, and answer delivery.
- [Chat service tests](../../../backend/tests/domain/assistant/services/test_chat_service.py) exercise reply recording, scope routing, the empty manuscript, and retrieval fallback. [Request tests](../../../backend/tests/domain/assistant/api/test_ask_request.py) cover the default source library scope and accepted scope values.
