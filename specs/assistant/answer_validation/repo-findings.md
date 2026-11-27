# Repo findings — assistant answer validation (#125)

## Pre-migration baseline

Before the migration, `ChatService.ask()` delegated scoped retrieval to `EvidenceRetriever`. Source Library answers used `SourceAnswerCandidates`, the pattern-based `local_evidence.py` checker and an optional Gemini proposal. The adapter exposed proposal, check and revision operations.

`ValidateAnswer` already tracked the validation deadline and pending claims. The route, client and chat panel could deliver an optional unverified draft separately from verified findings and citations. Saved conversation history alone did not establish whether an answer had passed review or which evidence had supported it.

## Implemented outcome

For a fresh Source Library question with retrieved passages, Gemini drafts once. The service can retrieve additional evidence before a separate Gemini call reviews the draft against the question and passages. Each exchange allows at most two generation attempts. An eligible exact cache hit reuses the reviewed answer and citations, and a successful search with no passages returns an insufficient-evidence message. Both cases use zero generation attempts. Search embeddings are counted separately. The scripted passage checker and its candidate-selection code were removed.

## Original migration plan

- Reuse the source-scoped retrieval and citation identities. Distinguish empty retrieval from missing dependencies or a failed lookup before testing the cache.
- Adapt the adapter and port in place for separate draft and review attempts. Count calls at the provider boundary in `test_generation_budget.py` using `generation_support.py`. Verify failures cannot dispatch an implicit third attempt.
- Add cache tests for successful reuse, configuration changes, recovered passages and authorization. Integrate at the normal chat entry point. Bootstrap should provide the bounded cache to the service.
- Preserve observable outcomes covered by `test_chat_validation.py`, `test_answer_validation.py`, route tests, `chat.spec.js` and `ChatPanel.spec.js`. Once migrated, inspect callers of `local_evidence.py`, `source_answer_candidates.py` and `revise_draft.py` before branch-only cleanup. Retain citation rendering and supported partial-answer coverage.

## Scenario-to-test mapping

The following are verification targets for the new design. T-001 covers the service/provider behaviors, T-002 covers delivery, and T-007 verifies the complete set.

- S-098 — Display a supported answer.
- S-099 — Withhold an answer to a different question.
- S-100 — Revise an overstated claim.
- S-101 — Correct a mismatched citation.
- S-102 — Retrieve missing evidence.
- S-103 — Explain a remaining gap after evidence recovery.
- S-104 — Show progress only when validation exceeds five seconds.
- S-105 — Return verified partial findings at the deadline.
- S-106 — Reach the deadline before any validation completes.
- S-107 — Withhold an entirely off-topic draft after review.
- S-108 — Explain an interrupted validation.
- S-109 — Distinguish the manuscript claim from what the selected report establishes.
- S-110 — Apply the deadline response when validation fails at exactly 30 seconds.
- S-111 — Reuse an exact fully reviewed answer.
- S-112 — Review which group a number describes.
- S-113 — Withhold an unsupported year even when the quote is genuine.
- S-114 — Count failed attempts without automatic retries.
- S-115 — Offer pending claims on request when validation runs out of time.
- S-116 — Withhold a draft with no eligible claims.
- S-117 — Require fresh review when reuse conditions change.
- S-118 — Retry an exchange that had no fully reviewed success.
- S-119 — Explain an empty search without generation.
- S-120 — Distinguish a failed search from an empty search.
