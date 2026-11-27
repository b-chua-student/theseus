# Design — Assistant chat safeguards

## Design

| ID | Decision | Components | Requirements |
| --- | --- | --- | --- |
| D-001 | Screen the writer’s incoming question after access and query validation, before opening an exchange. Recognize direct override and disclosure requests while allowing academic discussion of either topic. Surface a distinct prompt-injection error through the chat API. A rejection exits before retrieval, persistence, or model invocation. | Chat service, assistant errors, chat submission route | R-001, R-002 |
| D-002 | Apply the ten-per-minute limit to chat submission using the shared limiter and its existing remote-address key. Preserve existing broader limits. Let the application factory’s test setting govern enforcement so an explicit test override exercises the same route as normal traffic. | Chat submission route, shared limiter, application factory | R-003, R-004 |
| D-003 | Take the last ten entries of the aggregate’s chronologically ordered completed history at the service-to-model boundary. Pass that list to the model for the current reply. Keep persistence and conversation detail on the aggregate’s full history. | Chat service, conversation aggregate, model interface | R-005 |
| D-004 | Exercise service behavior with a recording fake model and rate limiting through the chat endpoint. Apply network blocking across the safeguard checks and use dummy credentials wherever provider configuration is needed. Keep requests within the same limit window using a controlled clock or equivalent deterministic setup. | Chat service tests, route tests, offline fixtures | R-001, R-002, R-003, R-004, R-005, R-006 |

## Components and Flow

The chat submission route applies the burst limit when enabled. A request over the limit receives a rate-limit error before the model is called. For an admitted request, the chat service checks access, validates the question, and screens its text before creating a pending exchange. A direct override or disclosure request returns a prompt-injection error at that point. An academic discussion proceeds through the ordinary reply path. The service supplies recent completed exchanges to the model, records the answer, and returns it to the writer.

## Data and Interfaces

The shared limiter counts submissions by the existing remote-address key. The screening input is the writer’s question before the service adds manuscript or retrieved context. The model receives the current query, applicable context, and up to ten prior completed exchanges ordered oldest first. The conversation repository and detail response retain the full history. Both limits apply uniformly across projects, and the application factory retains its explicit rate-limit override for tests.

## Evidence Outcomes

- Direct override and disclosure requests produce the expected error, zero model calls, and no change to the prior or pending exchanges. Both academic-question examples reach the model and return its answer.
- With limiting enabled, eleven ordinary submissions from one client in a fresh minute yield ten answers, one rate-limit error, and ten model calls. Under default test settings, all eleven receive answers.
- With ten prior exchanges, the model receives all ten. With eleven, it receives exchanges 2 through 11 in order, and all eleven prior exchanges remain available after reload.
- The safeguard checks exercise these outcomes with network connections blocked and live credentials absent.
