from dataclasses import dataclass

from domain.assistant.infrastructure.adapters.in_memory_conversation_repository import (
    InMemoryConversationRepository,
)
from domain.assistant.infrastructure.adapters.in_memory_indexed_document_repository import (
    InMemoryIndexedDocumentRepository,
)
from domain.assistant.infrastructure.adapters.in_process_index_job_queue import (
    InProcessIndexJobQueue,
)
from domain.assistant.infrastructure.ports.chat_model import ChatModel
from domain.assistant.infrastructure.ports.conversation_repository import ConversationRepository
from domain.assistant.infrastructure.ports.document_chunker import DocumentChunker
from domain.assistant.infrastructure.ports.document_parser import DocumentParser
from domain.assistant.infrastructure.ports.embedding_generator import EmbeddingGenerator
from domain.assistant.infrastructure.ports.index_job_queue import IndexJobQueue
from domain.assistant.infrastructure.ports.indexed_document_repository import (
    IndexedDocumentRepository,
)
from domain.assistant.infrastructure.ports.source_content_provider import SourceContentProvider
from domain.assistant.infrastructure.ports.vector_store import VectorStore
from domain.assistant.services.chat import ChatService
from domain.assistant.services.get_indexing_status import GetIndexingStatusService
from domain.assistant.services.handlers.on_manuscript_saved import OnManuscriptSaved
from domain.assistant.services.handlers.on_source_added import OnSourceAdded
from domain.assistant.services.handlers.on_source_removed import OnSourceRemoved
from domain.assistant.services.ingestion_worker import IngestionWorker
from domain.manuscript.models.events import ManuscriptSaved
from domain.src_lib.infrastructure.adapters.in_process_event_bus import InProcessEventBus
from domain.src_lib.models.events import SourceAdded, SourceRemoved


@dataclass(frozen=True)
class AssistantModule:
    """Wired assistant-context dependencies exposed to the application container.

    Optional members are None when the ports they depend on were not provided.
    """

    indexed_document_repository: IndexedDocumentRepository
    index_job_queue: IndexJobQueue
    document_parser: DocumentParser | None = None
    document_chunker: DocumentChunker | None = None
    embedding_generator: EmbeddingGenerator | None = None
    vector_store: VectorStore | None = None
    chat: ChatService | None = None
    indexing_status: GetIndexingStatusService | None = None


def build_assistant_module(
    event_bus: InProcessEventBus,
    indexed_document_repo: IndexedDocumentRepository | None = None,
    index_job_queue: IndexJobQueue | None = None,
    source_content_provider: SourceContentProvider | None = None,
    document_parser: DocumentParser | None = None,
    document_chunker: DocumentChunker | None = None,
    embedding_generator: EmbeddingGenerator | None = None,
    vector_store: VectorStore | None = None,
    conversation_repo: ConversationRepository | None = None,
    chat_model: ChatModel | None = None,
) -> AssistantModule:
    """Build the assistant module and subscribe its handlers to ``event_bus``.

    In-memory defaults are used for repositories and the job queue when not given. The
    ingestion worker is wired only if every indexing port is supplied, and chat only if
    ``chat_model`` is supplied.
    """
    indexed_document_repo = indexed_document_repo or InMemoryIndexedDocumentRepository()
    index_job_queue = index_job_queue or InProcessIndexJobQueue()
    conversation_repo = conversation_repo or InMemoryConversationRepository()

    # Wire cross-context event handlers onto the shared event bus.
    on_source_added = OnSourceAdded(
        repository=indexed_document_repo,
        queue=index_job_queue,
        provider=source_content_provider,  # type: ignore[arg-type]  # may be None in tests
    )
    on_source_removed = OnSourceRemoved(repository=indexed_document_repo)
    on_manuscript_saved = OnManuscriptSaved(
        repository=indexed_document_repo,
        queue=index_job_queue,
    )

    event_bus.subscribe(SourceAdded, on_source_added)
    event_bus.subscribe(SourceRemoved, on_source_removed)
    event_bus.subscribe(ManuscriptSaved, on_manuscript_saved)

    # Wire the IngestionWorker only when all five infrastructure ports are provided.
    # This lets existing tests and containers continue to work without real adapters.
    if (
        source_content_provider is not None
        and document_parser is not None
        and document_chunker is not None
        and embedding_generator is not None
        and vector_store is not None
    ):
        ingestion_worker = IngestionWorker(
            repository=indexed_document_repo,
            source_provider=source_content_provider,
            parser=document_parser,
            chunker=document_chunker,
            embedding_generator=embedding_generator,
            vector_store=vector_store,
        )
        index_job_queue.set_worker(ingestion_worker.process)

    # Wire the chat service only when a model is available. When no model is
    # injected (tests, or environments without a configured chat provider), chat
    # stays None and the conversation routes return a server error if called.
    chat: ChatService | None = None
    if chat_model is not None:
        chat = ChatService(
            repository=conversation_repo,
            model=chat_model,
            embedding_generator=embedding_generator,
            vector_store=vector_store,
            document_repository=indexed_document_repo,
        )

    return AssistantModule(
        indexed_document_repository=indexed_document_repo,
        index_job_queue=index_job_queue,
        document_parser=document_parser,
        document_chunker=document_chunker,
        embedding_generator=embedding_generator,
        vector_store=vector_store,
        chat=chat,
        indexing_status=GetIndexingStatusService(repository=indexed_document_repo),
    )
