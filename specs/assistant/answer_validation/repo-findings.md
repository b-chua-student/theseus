# Repo findings — assistant answer validation (#125)

## Current implementation

`ChatService.ask()` delegates scoped retrieval to `EvidenceRetriever`. Source-backed answers currently use `SourceAnswerCandidates`, the pattern-based `local_evidence.py` checker and an optional Gemini proposal. The Gemini adapter already exposes propose, check and revise operations. Current service tests reflect both the local path and older validator injection.

`ValidateAnswer` already owns a validation deadline and pending-claim state. The route, client and panel already carry an optional unverified draft separately from the answer and citations. Reuse the existing progress and deadline handling. Saved conversation history alone does not identify a fully reviewed success or all inputs that produced it.

## Changes needed for the approved ticket

- Reuse the source-scoped retrieval and citation identities. Distinguish empty retrieval from missing dependencies or a failed lookup before testing the cache.
- Adapt the adapter and port in place for separate draft and review attempts. Count calls at the provider boundary in `test_generation_budget.py` using `generation_support.py`. Verify failures cannot dispatch an implicit third attempt.
- Add cache tests for successful reuse, configuration changes, recovered passages and authorization. Integrate at the normal chat entry point. Bootstrap should provide the bounded cache to the service.
- Preserve observable outcomes covered by `test_chat_validation.py`, `test_answer_validation.py`, route tests, `chat.spec.js` and `ChatPanel.spec.js`. Once migrated, inspect callers of `local_evidence.py`, `source_answer_candidates.py` and `revise_draft.py` before branch-only cleanup. Retain citation rendering and supported partial-answer coverage.

## Scenario-to-test mapping

The following are verification targets for the new design. T-001 covers the service/provider behaviors, T-002 covers delivery, and T-007 verifies the complete set.

- S-001 — Display a supported answer.
- S-002 — Withhold an answer to a different question.
- S-003 — Revise an overstated claim.
- S-004 — Correct a mismatched citation.
- S-005 — Retrieve missing evidence.
- S-006 — Explain a remaining gap after evidence recovery.
- S-007 — Show progress only when validation exceeds five seconds.
- S-008 — Return verified partial findings at the deadline.
- S-009 — Reach the deadline before any validation completes.
- S-010 — Withhold an entirely off-topic draft after review.
- S-011 — Explain an interrupted validation.
- S-012 — Distinguish the manuscript claim from what the selected report establishes.
- S-013 — Apply the deadline response when validation fails at exactly 30 seconds.
- S-014 — Reuse an exact fully reviewed answer.
- S-015 — Review which group a number describes.
- S-016 — Withhold an unsupported year even when the quote is genuine.
- S-017 — Count failed attempts without automatic retries.
- S-018 — Offer pending claims on request when validation runs out of time.
- S-019 — Withhold a draft with no eligible claims.
- S-020 — Require fresh review when reuse conditions change.
- S-021 — Retry an exchange that had no fully reviewed success.
- S-022 — Explain an empty search without generation.
- S-023 — Distinguish a failed search from an empty search.
