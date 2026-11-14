# Design Document: AI Research Assistant (THESEUS-6)

## 1. Architectural Overview

The **AI Research Assistant** ([THES-160](https://theseus-inc.atlassian.net/browse/THES-160) / `THESEUS-6`) follows the **Layered Domain-Driven Design (DDD)** architecture established in `theseus/backend`. It decouples HTTP routing and Pydantic request/response validation (`api/`) from core domain aggregates, entities, value objects, and domain services (`domain/assistant/`), vector store and persistence abstractions (`repositories/`), and external LLM/embedding adapters (Google Gemini and ChromaDB/in-memory vector store wrappers).

### Architectural Constraints & Runtime Decisions ([THES-160](https://theseus-inc.atlassian.net/browse/THES-160))

* **Whole-Response Generation**: All answers from Google Gemini are returned whole; streaming/SSE token chunking is excluded.

* **In-Memory Runtime Vector Store**: While ChromaDB and PostgreSQL adapter classes exist in the codebase ([THES-162](https://theseus-inc.atlassian.net/browse/THES-162)), the runtime vector store wired for this epic is in-memory ([THES-160](https://theseus-inc.atlassian.net/browse/THES-160)).

* **Single-Provider Lock**: Google Gemini is the sole LLM and embedding provider; dynamic runtime switching across third-party LLM providers is out of scope ([THES-160](https://theseus-inc.atlassian.net/browse/THES-160)).

## 2. Layered Component Architecture

| Architectural Layer | Module / Path | Responsibility | Jira Ticket | 
| ----- | ----- | ----- | ----- | 
| **API Layer (Routes & Schemas)** | `api/routes/assistant.py` |  |  | 

`api/schemas/assistant_requests.py`

`api/schemas/assistant_responses.py` | Validates HTTP requests via Pydantic (`extra="forbid"`, `str_strip_whitespace=True`), invokes assistant services registered in `app.extensions`, maps domain/provider errors to HTTP status codes, and serializes DTO responses. | [THES-161](https://theseus-inc.atlassian.net/browse/THES-161), [THES-165](https://theseus-inc.atlassian.net/browse/THES-165) |
| **Domain Models & Interfaces** | `domain/assistant/aggregates.py`

`domain/assistant/entities.py`

`domain/assistant/value_objects.py`

`domain/assistant/interface.py`

`domain/assistant/exceptions.py` | Defines pure Python domain aggregates (`Conversation`), domain entities (`Exchange`, `IndexingStatus`), value objects (`DocumentChunk`, `IndexingState`, `Citation`), domain events (`ManuscriptSaved`, `SourceAdded`, `SourceRemoved`), and abstract repository/adapter protocols. | [THES-161](https://theseus-inc.atlassian.net/browse/THES-161) |
| **Assistant Domain Services** | `domain/assistant/services/chat.py`

`domain/assistant/services/get_indexing_status.py`

`domain/assistant/services/ingestion_worker.py` | Orchestrates RAG retrieval and Gemini response generation (`chat.py`), queries manuscript indexing states (`get_indexing_status.py`), and executes chunking + embedding pipelines (`ingestion_worker.py`). | [THES-160](https://theseus-inc.atlassian.net/browse/THES-160), [THES-163](https://theseus-inc.atlassian.net/browse/THES-163), [THES-164](https://theseus-inc.atlassian.net/browse/THES-164) |
| **Event Handlers** | `domain/assistant/services/handlers/on_manuscript_saved.py`

`domain/assistant/services/handlers/on_source_added.py`

`domain/assistant/services/handlers/on_source_removed.py` | Subscribes to `ManuscriptSaved`, `SourceAdded`, and `SourceRemoved` domain events and dispatches asynchronous indexing or de-indexing tasks to `ingestion_worker.py`. | [THES-160](https://theseus-inc.atlassian.net/browse/THES-160), [THES-163](https://theseus-inc.atlassian.net/browse/THES-163) |
| **Adapters & Repositories** | `repositories/assistant/`

• `in_memory_vector_store.py`

• `chroma_vector_store.py`

• `gemini_adapter.py`

• `conversation_repository.py` | Implements the vector store interface (in-memory active store + ChromaDB wrapper), Google Gemini embedding and chat completion adapters, and conversation/status persistence. | [THES-160](https://theseus-inc.atlassian.net/browse/THES-160), [THES-162](https://theseus-inc.atlassian.net/browse/THES-162) |

## 3. Domain Entities, Aggregates, Value Objects & Events ([THES-161](https://theseus-inc.atlassian.net/browse/THES-161))

Following Tactical DDD in `theseus/backend`, the `domain/assistant/` package separates identity-bearing **Entities** and **Aggregate Roots** from immutable **Value Objects** and **Domain Events**:

### 3.1 Aggregate Roots (`domain/assistant/aggregates.py`)

* **`Conversation` (Aggregate Root)**:

  * **Identity & Attributes**:

    * `id: UUID` — Unique identifier for the conversation session.

    * `manuscript_id: UUID` — Reference to the target `Manuscript` aggregate.

    * `exchanges: list[Exchange]` — Ordered collection of Q&A exchanges within this conversation.

    * `created_at: datetime` — Timestamp of conversation creation.

  * **Domain Invariants & Methods**:

    * `add_exchange(question: str, answer: str, retrieved_chunk_ids: list[str]) -> Exchange`: Validates that `question` and `answer` are non-empty, instantiates a new `Exchange` entity, appends it to `exchanges`, and returns it.

### 3.2 Domain Entities (`domain/assistant/entities.py`)

* **`Exchange` (Domain Entity)**:

  * **Identity & Attributes**:

    * `id: UUID` — Unique identifier for the individual question-and-answer turn.

    * `conversation_id: UUID` — Parent `Conversation` identifier.

    * `question: str` — Validated user prompt submitted to the assistant.

    * `answer: str` — Complete (non-streaming) response returned by Google Gemini.

    * `retrieved_chunk_ids: list[str]` — Identifiers of the `DocumentChunk` records retrieved via RAG to ground the answer.

    * `created_at: datetime` — Timestamp when the exchange was recorded.

  * **Domain Invariants**:

    * `question` and `answer` must not be empty or whitespace-only (`ValueError` raised on violation).

* **`IndexingStatus` (Domain Entity)**:

  * **Identity & Attributes**:

    * `manuscript_id: UUID` — Unique identifier of the manuscript being tracked.

    * `state: IndexingState` — Current lifecycle state (`PENDING`, `INDEXING`, `INDEXED`, `FAILED`).

    * `chunk_count: int` — Number of indexed chunks currently stored for the manuscript and its sources.

    * `updated_at: datetime` — Timestamp of the most recent indexing transition.

    * `error_message: str | None` — Diagnostic message populated when `state == IndexingState.FAILED`.

  * **Domain Methods**:

    * `mark_indexing() -> None`, `mark_indexed(chunk_count: int) -> None`, `mark_failed(error_message: str) -> None`.

### 3.3 Domain Value Objects (`domain/assistant/value_objects.py`)

* **`IndexingState` (Enum / Value Object)**:

  * Values: `PENDING` (`NOT_INDEXED`), `INDEXING`, `INDEXED`, `FAILED`.

* **`DocumentChunk` (Immutable Value Object)**:

  * `chunk_id: str` — Deterministic or generated identifier for the vector store entry.

  * `manuscript_id: UUID` — Target manuscript UUID.

  * `source_id: UUID | None` — `None` when chunked from the manuscript body; set to the source `UUID` when chunked from an attached reference source.

  * `content: str` — Raw text segment.

  * `chunk_index: int` — Zero-based positional index within the manuscript or source.

  * `embedding: tuple[float, ...]` (or `list[float]`) — Vector representation produced by the Gemini embedding adapter.

* **`Citation` (Immutable Value Object)**:

  * `chunk_id: str`, `source_id: UUID | None`, `excerpt: str` — Metadata referencing a retrieved chunk used to ground an `Exchange`.

### 3.4 Domain Events (`domain/assistant/events.py` / Event Contracts) ([THES-160](https://theseus-inc.atlassian.net/browse/THES-160), [THES-163](https://theseus-inc.atlassian.net/browse/THES-163))

* **`ManuscriptSaved`**: Carries `manuscript_id: UUID` and updated manuscript text/sections; triggers `on_manuscript_saved.py`.

* **`SourceAdded`**: Carries `manuscript_id: UUID`, `source_id: UUID`, and source text; triggers `on_source_added.py`.

* **`SourceRemoved`**: Carries `manuscript_id: UUID` and `source_id: UUID`; triggers `on_source_removed.py`.

### 3.5 API Pydantic Schemas (`api/schemas/`) ([THES-161](https://theseus-inc.atlassian.net/browse/THES-161), [THES-165](https://theseus-inc.atlassian.net/browse/THES-165))

* **`CreateConversationRequest(BaseModel)`**:

  * `model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)`

  * `manuscript_id: UUID`

* **`AskQuestionRequest(BaseModel)`**:

  * `model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)`

  * `question: str = Field(min_length=1)`

* **`IndexingStatusResponseDTO` / `ConversationResponseDTO` / `ExchangeResponseDTO`**:

  * Provide `.from_domain(...)` classmethods and `.to_dict()` serialization methods matching `ManuscriptResponseDTO`.

## 4. Key Service Workflows

### 4.1 Event-Driven Ingestion Pipeline ([THES-163](https://theseus-inc.atlassian.net/browse/THES-163))

1. **Manuscript Saved (`handlers/on_manuscript_saved.py`)**:

   * Receives `ManuscriptSaved(manuscript_id, content)`.

   * Delegates to `IngestionWorker.ingest_manuscript(manuscript_id, content)`:

     1. Sets `IndexingStatus` for `manuscript_id` to `INDEXING`.

     2. Splits `content` into overlapping or paragraph-bounded `DocumentChunk` segments.

     3. Calls `GeminiEmbeddingAdapter.embed_texts(chunks)` to obtain embedding vectors.

     4. Purges prior manuscript chunks (`source_id=None`) for `manuscript_id` in the vector store and inserts the new chunks.

     5. Updates `IndexingStatus` to `INDEXED` (or `FAILED` if a `ProviderError` / `ConfigurationError` occurs).

2. **Source Added (`handlers/on_source_added.py`)**:

   * Receives `SourceAdded(manuscript_id, source_id, content)`.

   * Delegates to `IngestionWorker.ingest_source(manuscript_id, source_id, content)` to chunk, embed, and upsert chunks tagged with `(manuscript_id, source_id)`.

3. **Source Removed (`handlers/on_source_removed.py`)**:

   * Receives `SourceRemoved(manuscript_id, source_id)`.

   * Delegates to `IngestionWorker.remove_source(manuscript_id, source_id)` to delete all vector store entries matching `(manuscript_id, source_id)`.

### 4.2 RAG Retrieval & Gemini Chat Service (`domain/assistant/services/chat.py`) ([THES-164](https://theseus-inc.atlassian.net/browse/THES-164))

1. Validates that the target `Conversation` exists in `ConversationRepository` (raising not-found error if missing).

2. Calls `GeminiEmbeddingAdapter.embed_query(question)` to compute the query vector.

3. Queries `VectorStore.search(manuscript_id=conversation.manuscript_id, query_embedding=query_vector, top_k=k)` to retrieve the top matching `DocumentChunk` items from both the manuscript and active sources.

4. Builds the prompt context combining:

   * System instructions grounding answers in the provided manuscript and source excerpts.

   * Prior `Exchange` turns within the same `Conversation`.

   * Retrieved `DocumentChunk` passages.

   * The user's `question`.

5. Invokes `GeminiChatAdapter.generate_answer(prompt)` to get the complete text response.

6. Calls `conversation.add_exchange(...)` and persists the updated aggregate in `ConversationRepository`.

7. Returns the newly created `Exchange`.

### 4.3 Indexing Status Service (`domain/assistant/services/get_indexing_status.py`) ([THES-163](https://theseus-inc.atlassian.net/browse/THES-163), [THES-165](https://theseus-inc.atlassian.net/browse/THES-165))

1. Looks up the manuscript's indexing record by `manuscript_id`.

2. Returns the `IndexingStatus` domain entity containing current state (`PENDING`, `INDEXING`, `INDEXED`, `FAILED`), chunk count, and any provider error details.

## 5. API Endpoints (`api/routes/assistant.py`) ([THES-165](https://theseus-inc.atlassian.net/browse/THES-165))

| HTTP Method & Route | Request Payload / Params | Success Response | Error Responses | Service Invoked | 
| ----- | ----- | ----- | ----- | ----- | 
| `GET /api/manuscripts/<manuscript_id>/indexing-status` *(or `/api/assistant/manuscripts/<manuscript_id>/status`)* | Path: `manuscript_id: UUID` | `200 OK` (`IndexingStatusResponseDTO`) | `400` Invalid UUID |  | 

`404` Manuscript not found | `get_indexing_status.py` |
| `POST /api/assistant/conversations` | Body: `CreateConversationRequest` (`manuscript_id`) | `201 Created` (`ConversationResponseDTO`) | `400` Validation error

`404` Manuscript not found | `chat.py` / Conversation creation |
| `POST /api/assistant/conversations/<conversation_id>/exchanges` *(or `/messages`)* | Path: `conversation_id: UUID`

Body: `AskQuestionRequest` (`question`) | `200 OK` / `201 Created` (`ExchangeResponseDTO`) | `400` Invalid UUID or empty question

`404` Conversation not found

`502`/`503` Provider or config error | `chat.py` |

## 6. Error Handling Matrix ([THES-160](https://theseus-inc.atlassian.net/browse/THES-160), [THES-164](https://theseus-inc.atlassian.net/browse/THES-164), [THES-165](https://theseus-inc.atlassian.net/browse/THES-165))

| Failure Scenario | Domain / Adapter Exception | State Impact | HTTP Status | 
| ----- | ----- | ----- | ----- | 
| Missing or invalid `GEMINI_API_KEY` | `AssistantConfigurationError` | No exchange persisted; ingestion status set to `FAILED` if triggered during indexing | `503 Service Unavailable` (or `500 Internal Server Error`) | 
| Gemini API timeout, rate limit, or 5xx error during chat | `AssistantProviderError` | `Conversation` remains unchanged (atomic failure before `add_exchange`) | `502 Bad Gateway` / `503 Service Unavailable` | 
| Gemini API failure during background ingestion | `AssistantProviderError` | `IndexingStatus` transitions to `FAILED` with error reason logged | Handled asynchronously; surfaced via `get_indexing_status.py` | 
| Invalid UUID path param or malformed JSON body | `ValueError` / Pydantic `ValidationError` | No service execution | `400 Bad Request` | 
| Unknown `manuscript_id` or `conversation_id` | `LookupError` / `ValueError` (Not Found) | No mutation | `404 Not Found` | 

## 7. Testing Strategy ([THES-166](https://theseus-inc.atlassian.net/browse/THES-166), [THES-167](https://theseus-inc.atlassian.net/browse/THES-167))

* **Unit Tests ([THES-166](https://theseus-inc.atlassian.net/browse/THES-166))**:

  * Domain invariants on `Conversation`, `Exchange`, `DocumentChunk`, and `IndexingStatus`.

  * `ingestion_worker.py` chunking boundaries, vector replacement on re-save, and status transitions (`INDEXING` -> `INDEXED` / `FAILED`) using fake embedding adapters and in-memory vector store.

  * `on_manuscript_saved.py`, `on_source_added.py`, and `on_source_removed.py` event dispatch and idempotency.

  * `chat.py` RAG top-k filtering by `manuscript_id`, prompt assembly, and provider/configuration error propagation.

* **Integration & End-to-End Tests ([THES-166](https://theseus-inc.atlassian.net/browse/THES-166), [THES-167](https://theseus-inc.atlassian.net/browse/THES-167))**:

  * Full lifecycle test ([THES-167](https://theseus-inc.atlassian.net/browse/THES-167)): Fire `ManuscriptSaved` and `SourceAdded` -> verify `get_indexing_status` returns `INDEXED` -> create a conversation via API -> post a question exchange -> verify RAG-grounded Gemini answer -> fire `SourceRemoved` -> verify removed source chunks are no longer retrieved.