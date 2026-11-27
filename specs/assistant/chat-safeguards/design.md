# Design: Assistant chat safeguards

## Design Decisions

| ID | Decision | Affected components | Requirements |
| --- | --- | --- | --- |
| D-001 | Screen the writer’s incoming question after access and query validation, before opening an exchange. Recognize direct override and disclosure requests while allowing academic discussion of either topic. Surface a distinct prompt-injection error through the chat API. A rejection exits before retrieval, persistence, or model invocation. | Chat service, assistant errors, chat submission route | R-001, R-002 |
| D-002 | Apply the ten-per-minute limit to chat submission using the shared limiter and its existing remote-address key. Preserve existing broader limits. Let the application factory’s test setting govern enforcement so an explicit test override exercises the same route as normal traffic. | Chat submission route, shared limiter, application factory | R-003, R-004 |
| D-003 | Take the last ten entries of the aggregate’s chronologically ordered completed history at the service-to-model boundary. Pass that list to the model for the current reply. Keep persistence and conversation detail on the aggregate’s full history. | Chat service, conversation aggregate, model interface | R-005 |
| D-004 | Exercise service behavior with a recording fake model and rate limiting through the chat endpoint. Apply network blocking across the safeguard checks and use dummy credentials wherever provider configuration is needed. Keep requests within the same limit window using a controlled clock or equivalent deterministic setup. | Chat service tests, route tests, offline fixtures | R-001, R-002, R-003, R-004, R-005, R-006 |
