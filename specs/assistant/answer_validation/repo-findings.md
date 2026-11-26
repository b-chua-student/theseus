# Repo findings — assistant answer validation (#125)

Codebase facts for implementing `tickets/assistant-answer-validation.md`. Verified against the working tree at base SHA `1dab3f5`. The older root `repo-findings.md` is stale (it claims the implementation was removed). Use this file for this feature.

Spec inputs: `specs/assistant/answer_validation/brief.md` and `gherkin.feature` (S-001 to S-013).

## 1. Where the feature plugs in

The single entry point is `ChatService.ask()` in `backend/domain/assistant/services/chat.py`.

Current flow, one pass with no validation:
1. Validate `context_scope` (`none`, `manuscript`, `source_library`; default `source_library`).
2. Load the `Conversation`, check project ownership via `get()`.
3. `conversation.ask(query)` opens a pending `Exchange`.
4. For `source_library`: `_retrieve()` returns `list[RetrievedChunk]`. For `manuscript`: the manuscript text is wrapped into the query. For `none`: no context.
5. `self._model.reply(history, model_query, context)` returns an `Answer`.
6. On `ChatModelError`: `conversation.discard_pending()` and re-raise. On any other exception: discard, log, raise `ChatModelError("The assistant failed to answer.")`.
7. `conversation.answer(exchange.id, answer)`, `repository.save(conversation)`, return the `Answer`.

Validation, revision and retries belong between steps 4 and 7. Only the final answer may be recorded on the exchange. Drafts and withheld drafts must never reach `conversation.answer()`.

### Retrieval, `ChatService._retrieve()`
- Needs `embedding_generator`, `vector_store`, `document_repository`, `source_ids` callable. If any is `None`, it returns `[]`.
- Embeds only the user's question (wrapped as a throwaway `Chunk`), then `vector_store.query(vector, k=top_k, doc_ref_ids=...)`. Default `top_k=5`.
- Filters to documents that are `is_searchable` and in the active source IDs, optionally narrowed by `source_ids` from the request.
- Catches every exception and returns `[]`. "No evidence" and "retrieval failed" are indistinguishable.
- It cannot search with a different query. S-005 (search again) needs a variant that accepts a query string, for example a missing-evidence query.

## 2. Domain model (`backend/domain/assistant/models/`)

- `Answer(text)`: frozen, stripped, non-blank (`EmptyAnswerError`). It has no citation data.
- `Query(text)`: frozen, stripped, non-blank.
- `RetrievedChunk(chunk_id, doc_ref_id, text, position, location, score)`. This is the unit of "passage". `location` is the displayed source location.
- `Chunk`, `Embedding`, `ChunkId`, `DocumentRefId`, `ProjectId`, `ConversationId`, `ExchangeId` are all frozen value objects.
- `Exchange`: `id`, `query`, `answer | None`, `asked_at`. `respond()` can be called once.
- `Conversation` (aggregate): at most one pending exchange. `ask()`, `discard_pending()`, `answer()`, `history` (answered only). Fields `context_scope` and `source_ids` are set after a successful answer.
- Errors (`models/errors.py`) extend `AssistantError(DomainError)` with a `code`: `ChatModelError` (`assistant.model_error`), `ChatModelRateLimitedError`, `ChatUnavailableError`, `EmptyAnswerError`, `PendingExchangeError`, `ConversationNotFoundError`.

### Gaps against the gherkin
| Need | Current state |
|---|---|
| Citation as data (S-001, S-004, S-005, S-006, S-012) | None. Citations exist only as text the model writes. The model sees passages as `[i] (location) text`. |
| Relevance, claim and citation checks | Not present. |
| Retry counter and limit (S-006, S-010) | Not present. The ticket requires two retries after the initial validation, shared by revision and retrieval (ticket lines 26). |
| Deadline (S-008, S-009, S-013) | Not present. The ticket requires 30 seconds for validation and all retries, starting when the first draft is ready to check (ticket lines 33-34). |
| Progress message (S-007) | Not present. The ticket requires "Checking the answer against your sources…" after five seconds, with draft text hidden (ticket line 27). The exchange request currently returns one JSON response. |
| Service-error outcome (S-011) | Not present. Today any model failure discards the pending exchange and raises `ChatModelError`. The ticket requires a specific message for a validation error before the deadline (ticket line 29). |
| Revision of a draft | Not present. |
| Re-search with a new query (S-005) | Not present, see section 1. |
| "No sources established" explanation (S-006) | Not present. `reply()` just answers. |

Domain code should stay free of Flask and Gemini imports. New value objects (for example a validation verdict, a cited passage reference, a retry budget) go in `models/value_objects.py`. New errors go in `models/errors.py`.

## 3. Ports and adapters (`infrastructure/`)

Existing ports (`ABC`, in `infrastructure/ports/`): `ChatModel`, `ConversationRepository`, `EmbeddingGenerator`, `VectorStore`, `IndexedDocumentRepository`, `DocumentChunker`, `DocumentParser`, `IndexJobQueue`, `SourceContentProvider`.

`ChatModel.reply(history, query, context=None) -> Answer` is the only model port. A validator or reviser needs a new port (for example under `infrastructure/ports/`) with:
- a real adapter backed by Gemini, next to `GeminiChatModel`;
- an in-memory or fake adapter for tests, since tests may not call Gemini.

`GeminiChatModel` details to reuse:
- Uses `google-genai` (`genai.Client`), model default `gemini-3-flash-preview`, timeout 30 s (`DEFAULT_TIMEOUT_MS`), reads `GEMINI_API_KEY`.
- Maps `APIError` 429 to `ChatModelRateLimitedError`, other errors to `ChatModelError`, and empty or blocked responses to `ChatModelError`.
- `_with_context()` formats context as `[i] (location) text` and prefixes "Use the following excerpts from the user's sources when relevant."

Each validation step adds model calls. The ticket fixes the budget at two retries and 30 seconds in total. The current client timeout is 30 s per call and is not tied to a request deadline, so a single call can outlast the remaining time. Adapter timeouts must be capped at the remaining time, and a blocking call cannot be cancelled, so late results must be ignored.

Retrieval adapters: `InMemoryVectorStore` (cosine similarity, dict-backed), `ChromaVectorStore`, `InMemoryEmbeddingGenerator`, `InMemoryIndexedDocumentRepository`. The in-memory ones are what tests use.

## 4. Wiring (`backend/bootstrap/`)

- `bootstrap/contexts/assistant/module.py`: `build_assistant_module(...)` creates `ChatService` only when `chat_model` is given. Retrieval ports are passed through from the container. New validator ports must be threaded through here, then `container.py` (`build_container()` and the Mongo variant).
- `bootstrap/app.py`: `_build_chat_model()` returns `GeminiChatModel()` unless `app.testing`. Tests get `chat_model=None`, so `chat` is `None` and the routes raise `ChatUnavailableError` (503).
- `bootstrap/error_handlers.py` maps `ChatUnavailableError` to 503, `ChatModelRateLimitedError` to a "busy" response, and `ChatModelError` to a "couldn't answer" response. Reuse these for validation failures. Add handlers only for new error types.
- Contexts talk through the in-process event bus. They must not import each other's services. `chat.py` already uses only assistant-context types.

## 5. API surface (`backend/domain/assistant/api/`)

- `POST /<project_id>/conversations/<conversation_id>/exchanges` (blueprint `conversation_bp`) calls `_chat().ask(...)` and returns `201 {answer: <text>}`. Paths are mounted by `bootstrap/app.py`; confirm the prefix there before documenting.
- `AskRequest` (Pydantic): `context_scope`, `source_ids` (max 1000), `manuscript_text` (max 500 000), `query` (1 to 4000, non-blank).
- Response is `answer.text` only. If citations become structured, the response shape changes. That is an API decision for `design.md`, and the frontend would need to follow.
- The request is synchronous and returns one JSON response today. Validation and retries add model calls, bounded by the ticket's 30-second deadline. The ticket requires a progress message after five seconds, so the response mechanism for progress is a design matter (D-006).
- Routes are guarded by `login_required` and project-membership checks. Rate limiting uses Flask-Limiter.

The frontend chat client was not inspected for this document.

## 6. Existing tests

- `backend/tests/domain/assistant/services/test_chat_service.py`: unit tests for `ChatService` with:
  - `FakeChatModel(answer, error)` that records `calls` and returns a canned `Answer`;
  - a `Library` helper wiring `InMemoryIndexedDocumentRepository`, `InMemoryVectorStore`, `InMemoryEmbeddingGenerator`.
- `backend/tests/domain/assistant/models/test_conversation_aggregate.py`, `backend/tests/domain/assistant/api/test_ask_request.py`.
- Constructing `ChatService(repository, model)` with only these two arguments must keep working. Existing tests rely on optional args.
- Add new tests beside these. Mirror the source paths (`tests/domain/assistant/...`, `tests/services/...`).

Scenario to test mapping (the gherkin uses fixed passages P1 to P3). Each needs a fake validator and a fake model returning scripted drafts, so tests can assert the displayed answer and which drafts were seen.
- S-001: scripted draft passes all checks, the answer is returned and saved.
- S-002: relevance fails, the draft is never returned or saved.
- S-003: claim check fails, revised draft is checked and returned.
- S-004: citation check fails, corrected citation (P2) is checked and returned.
- S-005: insufficient evidence, second search adds P2, the final answer cites P1 and P2.
- S-006: retry budget used up, no further retry, final answer cites P1 and states the end date is not established.
- S-007: service test is not needed. Route and chat-panel tests with a controllable clock assert no progress message through five seconds, then the progress message while validation is still pending, and no draft text at any point.
- S-008: controllable clock reaches 30 seconds while a retry waits for evidence. The answer has the verified May start citing P1 and explains the missing end date.
- S-009: clock reaches 30 seconds before the first check completes. The answer is the timeout message and the draft is hidden.
- S-010: three off-topic drafts with start and end dates established by checked passages. The answer is the relevance message, with no source-gap claim and no further retry.
- S-011: validator raises before the deadline. The pending exchange is discarded, the error message is returned and the draft is hidden.
- S-012: manuscript text says July 12, the report gives July only. The answer attributes July 12 to the manuscript and says the report leaves the day unverified.
- S-013: validator error at exactly 30 seconds, with and without verified findings. The deadline response is returned, not the service-error message.

## 7. Conventions and constraints

- Hexagonal layout, one use case per service file (`services/<name>.py`), models inward, ports and adapters in `infrastructure/`.
- Python 3.12, Flask 3.1, Pydantic 2.14. Pinned in `backend/requirements.txt`: `google-genai==2.33.0`, `chromadb==1.5.9`, `pydantic==2.14.1`. Avoid new heavy or unpinned dependencies.
- Ruff rules E, F, W, I, B, UP, SIM, A, T20, ANN, FBT, D (Google docstrings, 100-character lines). Mypy is strict (`disallow_any_explicit`, `warn_unreachable`). Note `FBT` rejects boolean positional parameters.
- Commands: `ruff check backend/`, `mypy backend/`, `pytest backend/` (pytest uses `--import-mode=importlib`).
- Tests use in-memory fakes only. No live MongoDB or Gemini key.
- `AGENTS.md`: Gherkin-derived tests are written and run before application code changes, and each test is tied to its `S-###` in `tasks.md`.
- Commit format: Commitizen, for example `feat(assistant): ...`.

## 8. Open items affecting implementation

Decided by the ticket (`tickets/assistant-answer-validation.md`, "Open Questions" says none remain):
- Two retries after the initial validation, shared by revision and retrieval (line 26).
- 30-second deadline from the first draft being ready, and the deadline outcomes (lines 33-34).
- Progress message after five seconds with the draft hidden (line 27).
- Off-topic exhaustion message (line 28) and service-error message (line 29).

Not in the ticket:
- Whether validation applies to the `none` and `manuscript` scopes. The ticket covers source-backed answers only. The existing code path to gate is `context_scope == "source_library"`. This stays a suggestion in `requirements.md` Open Questions.
Technical decisions for `design.md`:
- Citation representation: structured data or parsed from the model text.
- One validator port or separate ports (relevance, claims, citations, reviser).
- Retry budget: where it lives, and one budget shared by all retry kinds.
- Handling of "retrieval failed" vs "no relevant passages" (currently both `[]`).
- Pending exchange behavior on failure: keep the existing `discard_pending()` so users can ask again.

## 9. References

- Ticket: `tickets/assistant-answer-validation.md` (non-goal links `tickets/assistant-answer-evaluation.md`, which does not exist yet).
- Workflow: `AGENTS.md`, templates in `specs/templates/`.
- Note: this folder is `assistant-answer-validation`, but the brief and gherkin live in `specs/assistant/answer_validation/` (underscore, per the ticket's Output Paths).
