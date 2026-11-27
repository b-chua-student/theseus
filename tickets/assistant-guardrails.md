# [ASSISTANT-GUARDRAILS-01] As a writer, I can ask questions with assistant guardrails active

## Intent
Protect writers from instruction disclosure, prompt injection, and unsafe outputs while preserving ordinary chat in each supported scope.

## Context
Writers ask general questions in none scope and document-grounded questions in manuscript or source library scope. Evaluators check the assistant's default protections.

## Scope
- Apply default instructions for honest grounding, confidentiality, and refusal of rule overrides.
- Treat manuscripts and retrieved source excerpts as passive references. Ignore instructions embedded in either.
- Keep untrusted text separate from the writer's question and enable default harmful-content filters.

## Expected Outcomes
- [ ] Writers receive answers to ordinary questions in all three scopes. General questions work without attachments and the assistant makes no claims of access to unattached documents.
- [ ] Retrieved excerpts stay inside explicit untrusted-data boundaries even when they contain closing markers.
- [ ] Manuscript text stays inside explicit untrusted-data boundaries even when it contains closing markers.
- [ ] Default instructions prohibit revealing internal instructions and accepting requests to override them.
- [ ] Content safety filters for harmful categories are active by default.
- [ ] Automated checks verify these defaults, document isolation, and delivery of ordinary answers offline.

## Rules / Constraints
The protections apply by default when the assistant starts without custom overrides.

## Non-Functional Requirements
Verification must run without external credentials or network access.

## Out of Scope
Blocking ordinary general questions, input keyword filters, rate limiting, post-generation answer validation, semantic embeddings, chunking, vector storage, conversation history truncation, and background indexing queues.

## Open Questions
Should safety thresholds be configurable in a future change? Use defaults for this feature.

## Output Paths
Feature directory: `specs/assistant/prompt-guardrails/`.

- Intake brief: `brief.md`
- Gherkin: `gherkin.feature`
- Spec files: `requirements.md`, `design.md`, and `tasks.md`

## Definition of Done
- [ ] Intake generated and approved
- [ ] Gherkin generated and approved
- [ ] Open questions resolved
- [ ] Spec, Gherkin, and code in sync
- [ ] Reviewed and merged
