# Implementation Plan (`tasks.md`): AI Research Assistant (THESEUS-6)

> **Epic Reference:** [THES-160 — AI Research Assistant](https://theseus-inc.atlassian.net/browse/THES-160) (`THESEUS-6`)  
> **Key Services Scope:** `domain/assistant/services/` (`chat.py`, `get_indexing_status.py`, `ingestion_worker.py`, and `handlers/on_manuscript_saved.py`, `on_source_added.py`, `on_source_removed.py`)

## Task Breakdown

- [ ] 1. Setup Assistant domain models and schemas ([THES-161](https://theseus-inc.atlassian.net/browse/THES-161))
  - [ ] 1.1 Define Assistant domain value objects and enums (`IndexingState`, `IndexingStatus`, `DocumentChunk`, `Citation`) in `domain/assistant/value_objects.py`
  - [ ] 1.2 Implement `Exchange` entity and `Conversation` aggregate root in `domain/assistant/entities.py` and `domain/assistant/aggregates.py`
  - [ ] 1.3 Define abstract contracts (`AbstractConversation`, vector store protocol, embedding/chat provider interfaces, and domain exceptions) in `domain/assistant/interface.py`
  - [ ] 1.4 Create Pydantic request schemas (`CreateConversationRequest`, `AskQuestionRequest`) and response DTOs (`IndexingStatusResponseDTO`, `ConversationResponseDTO`, `ExchangeResponseDTO`) in `api/schemas/`
  - _Requirements: Requirement 3, Requirement 4, Requirement 5_

- [ ] 2. Implement ChromaDB vector store wrapper and Gemini embedding adapter ([THES-162](https://theseus-inc.atlassian.net/browse/THES-162))
  - [ ] 2.1 Implement the in-memory vector store (`InMemoryVectorStore`) for runtime similarity search and metadata filtering by `manuscript_id` and `source_id`
  - [ ] 2.2 Implement the ChromaDB vector store wrapper (`ChromaVectorStore`) conforming to the same vector store interface (kept unwired in production runtime per [THES-160](https://theseus-inc.atlassian.net/browse/THES-160) scope)
  - [ ] 2.3 Implement the Google Gemini embedding adapter (`GeminiEmbeddingAdapter`) with configuration validation and provider-error wrapping
  - _Requirements: Requirement 1, Requirement 2, Requirement 5, Requirement 6_

- [ ] 3. Implement manuscript & source ingestion handlers and worker ([THES-163](https://theseus-inc.atlassian.net/browse/THES-163))
  - [ ] 3.1 Implement `domain/assistant/services/ingestion_worker.py` to chunk manuscript and source text, generate embeddings, update the vector store, and transition manuscript indexing status (`INDEXING` -> `INDEXED` / `FAILED`)
  - [ ] 3.2 Implement `domain/assistant/services/handlers/on_manuscript_saved.py` to handle `ManuscriptSaved` events and trigger manuscript re-indexing
  - [ ] 3.3 Implement `domain/assistant/services/handlers/on_source_added.py` to handle `SourceAdded` events and index attached source content
  - [ ] 3.4 Implement `domain/assistant/services/handlers/on_source_removed.py` to handle `SourceRemoved` events and purge matching `source_id` chunks from the vector store
  - [ ] 3.5 Implement `domain/assistant/services/get_indexing_status.py` to report current manuscript indexing status and chunk metadata
  - _Requirements: Requirement 1, Requirement 2, Requirement 3, Requirement 6_

- [ ] 4. Implement RAG search service & Gemini chat integration ([THES-164](https://theseus-inc.atlassian.net/browse/THES-164))
  - [ ] 4.1 Implement the Google Gemini chat completion adapter (`GeminiChatAdapter`) returning whole (non-streaming) answers and mapping missing API keys or upstream failures to typed exceptions
  - [ ] 4.2 Implement `domain/assistant/services/chat.py` to manage conversation creation, embed user questions, retrieve top-k relevant manuscript/source chunks, assemble grounded RAG prompts, generate answers via Gemini, and persist `Exchange` records
  - _Requirements: Requirement 4, Requirement 5, Requirement 6_

- [ ] 5. Implement Assistant API endpoints ([THES-165](https://theseus-inc.atlassian.net/browse/THES-165))
  - [ ] 5.1 Create Flask Blueprint routes in `api/routes/assistant.py` for querying indexing status, creating conversations, and posting question exchanges
  - [ ] 5.2 Wire Pydantic request validation (`400`), not-found handling (`404`), and provider/configuration error handling (`502`/`503`)
  - [ ] 5.3 Register the in-memory vector store, Gemini adapters, event handlers, and assistant services in `api/app.py` (`app.extensions`)
  - _Requirements: Requirement 3, Requirement 4, Requirement 5, Requirement 6_

- [ ] 6. Unit and integration tests for Assistant domain ([THES-166](https://theseus-inc.atlassian.net/browse/THES-166))
  - [ ] 6.1 Write unit tests for `Conversation`, `Exchange`, `IndexingStatus`, and Pydantic request/response schemas
  - [ ] 6.2 Write unit tests for `ingestion_worker.py` and event handlers (`on_manuscript_saved.py`, `on_source_added.py`, `on_source_removed.py`) including failure and idempotency cases
  - [ ] 6.3 Write unit and service-level integration tests for `chat.py` and `get_indexing_status.py` covering RAG retrieval, empty context fallback, configuration errors, and provider failures
  - _Requirements: Requirement 1, Requirement 2, Requirement 3, Requirement 4, Requirement 5, Requirement 6_

- [ ] 7. End-to-end integration test for AI Research Assistant flow ([THES-167](https://theseus-inc.atlassian.net/browse/THES-167))
  - [ ] 7.1 Implement end-to-end test covering `ManuscriptSaved` -> `SourceAdded` -> indexing status verification (`INDEXED`) -> conversation creation -> RAG question/answer exchange -> `SourceRemoved` de-indexing verification
  - _Requirements: Requirement 1, Requirement 2, Requirement 3, Requirement 4, Requirement 5, Requirement 6_