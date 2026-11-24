# Repo findings: assistant combined context (issue #120)

Facts about the current code that matter for implementing `brief.md` and `gherkin.feature` in this folder. Verified by reading the files named below on branch `feat/assistant-combined-context`.

The root `repo-findings.md` is out of date. It says the implementation was removed, but `backend/domain/**` is present. Use this file instead.

## 1. Repository conventions

- Backend: Python 3.12, Flask 3.1, Pydantic 2.14. Hexagonal layout per context under `backend/domain/<context>/` with `api/`, `services/`, `models/`, `infrastructure/ports/` and `infrastructure/adapters/`.
- Contexts talk through the in-process event bus. They do not import each other's services. The assistant context already imports `src_lib` events and value objects in `bootstrap/contexts/assistant/module.py`.
- Composition root: `backend/bootstrap/container.py` (`build_container` for in-memory, `build_mongo_container` for MongoDB) and `backend/bootstrap/contexts/assistant/module.py`.
- Lint and types: `ruff check backend/` (Google docstrings, 100-column lines, `ANN`, `FBT` and `D` enabled) and `mypy backend/` (strict, `disallow_any_explicit`). Run `ruff check`, `mypy` and `pytest` once each after changes, as `workflow` requires.
- Dependencies are pinned in `backend/requirements.txt`, and dev tools are in `requirements-dev.txt`. `hypothesis` is available. `pytest-bdd` is not installed and there is no Cucumber runner. Decide how the `.feature` file is executed before writing step definitions. AGENTS.md says "Write step definitions before application code".
- Tests use in-memory fakes only (no live MongoDB or Gemini). Backend tests mirror source paths under `backend/tests/domain/<context>/`. Existing assistant tests: `tests/domain/assistant/services/test_chat_service.py`, `.../api/test_ask_request.py` and `.../models/test_conversation_aggregate.py`. `FakeChatModel` and the `Library` helper in `test_chat_service.py` are the pattern to extend. Add `@pytest.mark.integration` to integration tests; the marker is registered in `pyproject.toml`.
- Frontend tests: `*.spec.js` run under Vitest (`npm run test:components`, Svelte Testing Library). `*.test.js` run under Node's runner (`npm test`). `docs/ai-test-context.md` says to select controls by accessible role and name.
- Gherkin lint (`.gherkin-lintrc`): every scenario needs an `@S-###` tag and an `@criterion-#` tag, at most 8 steps per scenario (5 in Background), scenario names of 100 characters or fewer, and `use-and`, `only-one-when` and indentation rules apply. Changes to the `.feature` file must keep passing it.

## 2. Backend: where the feature lands

### API contract today (`backend/domain/assistant/api/requests.py`, `routes.py`)

- Route: `POST /api/projects/<project_id>/conversations/<conversation_id>/exchanges`. It returns `201 {answer}`. Other routes in the same blueprint are `GET ""` (list), `GET "/<id>"` (with exchanges) and `POST ""` (start).
- `AskRequest` fields: `context_scope` (`"none" | "manuscript" | "source_library"`, default `"source_library"`), `source_ids` (`list[UUID] | None`, **`max_length=1000`**), `manuscript_text` (max 500,000 characters) and `query` (1 to 4000 characters, not blank).
- A pydantic `ValidationError` becomes `400 {error, details}`.
- Every scope is one value, so it cannot express Web + Manuscript + sources. The brief requires "A combined selection must convey all active choices" and Web alone mapping to `none` (S-080: scope `none`, empty manuscript text, null source IDs). The wire format is a design decision. The new request fields must stay backward compatible with `test_ask_request.py` unless that test is deliberately changed.
- There is no field for a quote. S-075 and S-088 need the quote as its own item, separate from `query`.
- The 1,000-ID cap blocks S-092 (1,001 sources). Raise or remove it, or send a selection form that doesn't enumerate IDs. This is a design decision. `source_ids` are validated as UUIDs.
- `check_project_access` (a `before_request` on `conversation_bp`) returns 401 for no session and 404 when the user is not a project member. `login_required` is applied per route.
- `_conversation_json` returns `context_scope` and `source_ids` per conversation. The frontend uses them to restore state.
- Errors are domain exceptions (`DomainError` with `code`) translated in `backend/bootstrap/error_handlers.py`. The frontend reads `e.status` and `e.code`.

### Chat service (`backend/domain/assistant/services/chat.py`)

- `ChatService.ask(conversation_id, text, context_scope, source_ids, manuscript_text, project_id)` does the following:
  - Opens a pending exchange.
  - Retrieves chunks only when `context_scope == "source_library"`.
  - For `"manuscript"`, wraps the question text as `Current manuscript:\n...\n\nQuestion: ...`.
  - Calls `ChatModel.reply(history, query, context)`.
  - On success sets `conversation.context_scope` and `conversation.source_ids` and saves. On failure it calls `discard_pending()` and re-raises without saving.
- Saving only after success matches S-090 (restore the selection from the last **successful** exchange). Keep that ordering for any new Web and Manuscript fields.
- Manuscript and source retrieval are mutually exclusive today (one scope value). Combining them requires restructuring `ask` and `_retrieve`.
- `_retrieve` has these properties:
  - It embeds the question by wrapping it in a throwaway `Chunk` and calling `EmbeddingGenerator.generate`.
  - It calls `VectorStore.query(vector, k=self._top_k, doc_ref_ids=...)` with `top_k=5` **across all selected documents together**. One source with many matches can crowd out the others (violates S-094).
  - It has **no relevance threshold** (S-095) and no per-source accounting.
  - It filters out any document that is not `is_searchable`, silently. A not-yet-indexed source is simply skipped.
  - It wraps the whole call in `except Exception` and returns `[]`. A vector store failure cannot currently be reported per source (S-072, S-073, S-079 need `unavailable`).
  - It returns `[]` when no source IDs are configured.
- Existing cross-project protection (S-077): `allowed = set(self._source_ids(project_id))`, then it intersects with the requested IDs. `source_ids` is a lambda in `container.py` that returns active (`list_active()`) sources whose `project_id` matches. Foreign IDs are therefore already dropped. The test for S-077 should assert that no foreign passage reaches the model, and that its vector store query never lists the foreign ID.
- `source_ids is None` currently means "all active sources in the project". The brief's "All indexed sources" snapshots the set at selection time, so a null selection must not remain a floating "all" (S-093).
- `ChatService` is one class in one file. `structure.md` prefers one use case per file. New retrieval or budget logic can go in separate service modules or helpers without growing `chat.py` further.

### Chat model port and Gemini adapter

- Port: `ChatModel.reply(history: list[Exchange], query: Query, context: list[RetrievedChunk] | None) -> Answer` (`infrastructure/ports/chat_model.py`).
- `RetrievedChunk` has `chunk_id`, `doc_ref_id`, `text`, `position`, `location` and `score`. It has **no source title**.
- `GeminiChatModel._with_context` formats `[i] (location) text` and says "Use the following excerpts from the user's sources when relevant". It does not name the source. The brief requires attributing each finding to a source, so titles must be available to the model.
- The port cannot carry per-source outcomes (unavailable, searched without a match, omitted for capacity), the quote, or a "Web enabled" flag. The port signature, a context object, or a richer prompt builder must change. Fakes in `test_chat_service.py` (`FakeChatModel.calls` tuple) will need updating.
- The model is `gemini-3-flash-preview` with `system_instruction=None` and a 30 s timeout. There is no token counting or context-window knowledge in the code. The brief says "fit retrieved evidence into the model's available context window" (S-096). A token-estimation or Gemini `count_tokens` approach has to be chosen, along with the budget size.
- Web in the brief is general chat from model knowledge with no live browsing. With Web off, the prompt must tell the model not to use general knowledge for factual findings (S-084, S-085). The Gemini adapter currently gives no such instruction.

### Retrieval infrastructure

- `VectorStore.query` returns top `k` results for a list of `doc_ref_ids`, each with `score` = cosine similarity (`ChromaVectorStore` returns `1 - distance` using a cosine HNSW space. `InMemoryVectorStore` computes cosine directly). A threshold filter can use `RetrievedChunk.score`.
- To give every source a chance, query per source (or per batch) rather than once with a global `k`. Chroma accepts a `$in` filter on `doc_ref_id`, so batching is possible. Source counts above 1,000 need batching in the request or the query (S-092).
- **Embeddings are not semantic in the default wiring.** `build_container` defaults to `InMemoryEmbeddingGenerator` (SHA-256 hash to a 32-dim vector, documented "NOT semantically meaningful") and `InMemoryVectorStore`. `app.py` passes only `chat_model` to the container. There is no production embedding adapter in the repo, although `google-genai` is installed. A meaningful relevance threshold needs a real embedding generator. The calibration the brief calls for cannot be done with the hash embedder. This is the largest gap.
- The vector store also contains chunks for manuscripts (the `OnManuscriptSaved` handler indexes saved manuscripts under the manuscript ID). `_retrieve` excludes them only because it intersects with library source IDs. Keep that intersection. The Manuscript context must use the live editor text sent at send time, not indexed (saved) manuscript chunks.
- `IndexedDocument` (`models/aggregates.py`) has a status lifecycle `PENDING -> INDEXING -> INDEXED | FAILED` and `is_searchable == INDEXED`. This is the basis for "indexed source" and for "unavailable". It also carries `title` (an `IndexedDocumentTitle`; file sources get `file_ref` as a placeholder title, text sources get the real title via `SourceContentProvider.get_title`).
- Source titles live on `Source.title` (`src_lib`). Source identity is `Source.id`, and `DocumentRefId(source.id.value)` is the assistant's reference. This matches the brief's "source identity follows the library entry ID".
- Sources are soft-deleted (`Source.remove()`, `is_removed`). `list_active()` excludes them. For S-091 (name a source that has since been removed) you need the title of a removed source. Check whether `SourceRepository.get()` still returns removed sources, and what `OnSourceRemoved` does to the `IndexedDocument` and vector store before relying on either one.

### Conversation model and persistence

- `Conversation` (`models/aggregates.py`) stores `context_scope: str = "source_library"` and `source_ids: list[str] | None` **once per conversation**, overwritten by the latest successful `ask`. `Exchange` stores only `query`, `answer` and `asked_at`.
- S-090 and S-091 ("last successful exchange") are met by conversation-level fields as long as they are written only after success. Web and Manuscript flags need new persisted fields on `Conversation`, in both repositories and in `_conversation_json`.
- `MongoConversationRepository._to_doc` and `_to_conversation` map the fields explicitly and default missing `context_scope` to `"source_library"`. New fields need defaults for old documents. `InMemoryConversationRepository` stores the object directly.
- Legacy mapping to decide: a saved `none` is Web. A saved `manuscript` and a saved `source_library` with `source_ids=None` (meaning all sources) each need a defined restored state. The brief says Web alone maps to `none` "including when displaying a saved record with that scope".
- The quote is not stored anywhere. Decide whether it is persisted with the exchange.

## 3. Frontend: where the feature lands

The only chat UI is `frontend/src/components/chat/ChatPanel.svelte`, mounted from `frontend/src/pages/editor.svelte` (`<ChatPanel projectId editor tick open onclose bind:notice />`). API client: `frontend/src/lib/api/chat.js`. Source list client: `frontend/src/lib/api/sources.js`.

Current behavior that conflicts with the brief:

- **Three scope buttons** (None, Manuscript, Source Library) and a separate "Select sources" picker that opens only for Source Library. The brief replaces this with one Context dropdown containing Web, Manuscript, sources, a Clear selection action, a title filter and an "All indexed sources" checkbox.
- **One conversation per scope.** `sessions` is keyed by `sessionKey` (scope, plus the sorted source IDs for `source_library`). The UI text says "Changing sources starts a separate conversation." The brief and S-076 require one conversation across context changes, so `sessions` must stop being keyed by selection.
- `contextScope` starts at `'none'`, which already matches "New chats start on Web".
- `ask()` sends `manuscript_text` from `editor.getText()` **only when** scope is `manuscript`. It sends `source_ids` only for `source_library`. Both need to follow the new checkbox state.
- **The quote is pasted into the textarea**: `quoteSelection()` stores `selectionQuote`, and `useQuote()` appends `Selected passage:\n<quote>` to `input`. The quote is therefore part of the question text, which contradicts S-075 and S-088. It must be sent as its own field. S-089 also requires that quoting does not change the selection (today nothing changes the scope, so only preserve that).
- `openConversation` restores `contextScope` and `selectedSourceIds` from `conversation.context_scope` and `conversation.source_ids`. Restoring Web and Manuscript, and naming an unavailable source (S-091), needs the new fields and a source lookup.
- `listSources(projectId)` calls `GET /api/sources?projectId=...` and returns `{id, kind, title, authors, year, file_ref}`. **It has no indexing status**, and it is the only source list the chat has. "All indexed sources" and the disabled state when nothing is indexed (S-081, S-083) need an indexed flag per source, or a new endpoint or field. The existing `indexing-status` endpoint is manuscript-only.
- Keyboard behavior in the brief (arrow keys, Space, Escape returning focus to the Context button; S-071) has no precedent in this component. The `source-options` list is plain labelled checkboxes.
- Rendering: replies go through `marked` and `DOMPurify` (`renderMarkdown`). Keep that for any new answer content.
- `send()` / `ask()` handle `404 assistant.conversation_not_found` by starting a new conversation. Keep that behavior in mind for S-076 (same conversation across changes).
- `apiFetch` (`frontend/src/lib/api/http.js`) throws errors with `status` and `code`.
- No existing spec file covers `ChatPanel`. Related component specs for patterns: `frontend/src/components/text-sources/*.spec.js` and `components/editor/EditorHeader.spec.js`.

## 4. Scenario-to-code map

| Area | Scenarios | Main files |
|------|-----------|------------|
| Dropdown selection rules (frontend, component) | S-063 to S-066, S-071, S-074, S-076, S-080 to S-083, S-086, S-087, S-089 to S-091 | `ChatPanel.svelte` (or a new Context dropdown component), `chat.js`, `sources.js` |
| Request shape (frontend sends, backend validates) | S-064, S-067, S-075, S-080, S-088 | `requests.py`, `routes.py`, `chat.js` |
| Retrieval rules (service) | S-070, S-077, S-079, S-092 to S-096 | `chat.py` and `_retrieve`, `VectorStore`, `container.py` |
| Prompt and answer behavior (acceptance) | S-068, S-069, S-072, S-073, S-078, S-084, S-085 | `chat.py`, `ChatModel` port, `gemini_chat_model.py` |
| Saved conversations | S-090, S-091 | `aggregates.py`, both conversation repositories, `routes.py`, `ChatPanel.svelte` |

The acceptance scenarios depend on real model output. Automated tests must use a fake `ChatModel` and assert on what it **receives** (draft text, quote, selected source IDs, per-source status, passages). Judging the wording of a real Gemini answer is a manual or evaluation step.

## 5. Open points the code does not settle

These are decisions or gaps, not requirements (AGENTS.md: anything not in the ticket goes under Open Questions).

1. Wire format for a combined selection and for the quote, and whether to raise the 1,000-ID cap (S-092).
2. A real embedding generator is needed before a relevance threshold can be calibrated (only the hash embedder exists).
3. Port change to carry source titles, per-source outcomes (`unavailable`, `searched without a match`, `matched but omitted for capacity`), the quote and a Web flag.
4. How the context budget is measured (token counting) and how passages are prioritized when the budget is tight.
5. Where the frontend gets "indexed" status for sources (needed for All indexed sources and its disabled state).
6. How to tell "unavailable" apart from "searched without a match" now that `_retrieve` swallows all exceptions and silently skips non-searchable documents.
7. Persistence and migration of the new Web and Manuscript flags, and legacy scope mapping for old conversations.
8. How `.feature` scenarios are executed (no BDD runner is installed).
