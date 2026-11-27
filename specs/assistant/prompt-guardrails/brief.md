# Brief: Assistant Prompt Guardrails and Safety Controls

- ID: ASSISTANT-GUARDRAILS-01
- Owner: AI Engineer (Theseus)
- Date: 2026-11-27
- Base SHA: 5204c40bb38c803184f184532ef4be4a3e3ebee5

## Goal

Protect the Theseus AI assistant across all three context scopes (none, manuscript, and source library) against direct and indirect prompt injection, instruction disclosure, and unsafe outputs while keeping general questions working in none scope.

## Users / Roles

- Writer asking general questions in none scope or document-grounded questions in manuscript or source library scope.
- Evaluator testing the assistant with direct and indirect prompt-injection attempts.

## In Scope

- Define a default system instruction enforcing resistance to rule overrides and jailbreaks, confidentiality of internal instructions, honest grounding (never fabricating claims about unattached documents in none scope), and treating attached documents as passive data.
- Isolate retrieved source excerpts and manuscript text from the user question using explicit untrusted-data boundaries.
- Neutralize boundary-escape attempts embedded inside retrieved source excerpts or manuscript text.
- Enable default content safety filtering across harmful content categories on assistant responses.
- Verify all guardrail behaviors through offline automated tests without live external model calls.

## Non-Goals

- Blocking normal general questions in none context scope.
- Input keyword filters or request rate limiting (handled in a separate gap).
- Post-generation answer validation pipelines handled in separate branches.
- Semantic embedding generation, document chunking, vector store wiring, history truncation, or background indexing queues.

## Constraints

- System instructions and content safety filters must be active by default whenever the assistant model is initialized without explicit overrides.
- Untrusted source excerpts and manuscript text must be treated strictly as passive reference data, never as executable instructions.
- Normal general questions in none scope and document-grounded questions in manuscript or source library scope must continue to receive helpful answers.
- Automated verification must not require live external credentials or network access.

## Known Touchpoints

- Assistant chat model adapter initialization and retrieved-context formatting.
- Assistant chat service manuscript-scope prompt assembly.
- Assistant unit test suite for chat model configuration and chat service behavior.

## Assumptions

- The assistant supports three context scopes: none (general chat), manuscript, and source library.
- Pending branches for combined context and answer validation will be reconciled separately on staging.

## Open Questions

- Should safety filter thresholds be configurable via environment settings? Deferred: apply safe defaults first and add configuration later if needed.

## Success Criteria

1. The assistant initializes with a default system instruction enforcing rule-override resistance, instruction confidentiality, honest grounding across all scopes, and general-question support in none scope.
2. Retrieved source excerpts in source library scope are wrapped in explicit untrusted-data boundaries separated from the user question, with embedded closing-boundary text neutralized.
3. Manuscript text in manuscript scope is wrapped in explicit untrusted-data boundaries separated from the user question, with embedded closing-boundary text neutralized.
4. Model-level content safety filters are enabled by default for harmful content categories.
5. Automated offline tests verify default system instructions, safety filter configuration, and untrusted-data boundary isolation without live external calls.

## Reference Links

- Repository SDD workflow: AGENTS.md