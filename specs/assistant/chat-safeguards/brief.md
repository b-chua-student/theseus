# Brief: Assistant Input Guardrails, Chat Rate Limit, and History Cap

- ID: ASSISTANT-SAFEGUARDS-02
- Owner: AI Engineer (Theseus)
- Date: 2026-11-27
- Base SHA: 1fbcb6d0025fc50df9c3bd392c25ab5367d85d21

## Goal

Protect the Theseus AI assistant and its provider quota before model calls by blocking obvious direct prompt-injection inputs, enforcing a per-minute burst rate limit on chat questions, and capping the number of prior exchanges forwarded to the model.

## Users / Roles

- Writer having multi-turn conversations with the assistant across any context scope.
- Evaluator attempting direct prompt-injection attacks or rapid burst requests against the assistant.

## In Scope

- Screen incoming chat questions for high-confidence direct prompt-injection override and system-prompt extraction attempts before calling the chat model.
- Reject flagged prompt-injection inputs with a clear error without invoking the chat model or saving the attack into conversation history.
- Allow benign academic questions that merely discuss prompt injection or system prompts to proceed normally.
- Enforce a default burst limit of ten questions per minute on submitting chat questions while keeping automated test runs unaffected unless rate limiting is explicitly enabled.
- Cap the conversation history forwarded to the model to the most recent ten completed exchanges by default while preserving full stored conversation history.
- Verify all safeguard behaviors through offline automated tests without live external credentials.

## Non-Goals

- Semantic embedding generation, document chunking, or vector store wiring.
- Post-generation answer validation pipelines handled in separate branches.
- Changing system instructions, untrusted-data boundaries, or content safety filters from ASSISTANT-GUARDRAILS-01.
- Background indexing queues or document parsing.

## Constraints

- Blocked prompt-injection requests must make zero calls to the external chat model and must not leave a pending exchange or persist the rejected query in conversation history.
- Benign questions containing security or AI terminology must not be falsely rejected.
- Capping forwarded history must preserve chronological order of the retained most recent exchanges and keep older exchanges intact in storage.
- Automated verification must run offline without live external credentials or network access.

## Known Touchpoints

- Incoming chat questions, conversation history, and offline safeguard checks.

## Assumptions

- None beyond the ticket.

## Open Questions

- Should the burst rate limit or history window be configurable per project? Deferred: this release uses the stated defaults.

## Success Criteria

1. High-confidence direct prompt-injection override and instruction-disclosure queries are rejected before calling the model, without polluting conversation history, while benign questions about AI security still succeed.
2. With limiting enabled, the first ten ordinary questions in a fresh minute succeed and the eleventh receives a rate-limit error before a model call. Automated runs accept the same burst unless limiting is explicitly enabled.
3. Conversations longer than the default ten-exchange history cap forward only the most recent completed exchanges in order while keeping full history stored.
4. Automated offline tests verify input blocking, benign pass-through, burst rate limiting, and history capping without live external calls.

## Reference Links

- Source ticket: [assistant-safeguards.md](../../../tickets/assistant-safeguards.md)
- Prior guardrail spec: specs/assistant/prompt-guardrails/brief.md
- Repository SDD workflow: AGENTS.md
