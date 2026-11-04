from dataclasses import dataclass
from typing import Any

from bootstrap.contexts.assistant.module import AssistantModule, build_assistant_module
from bootstrap.contexts.revision_history.module import (
    RevisionHistoryModule,
    build_revision_history_module,
)
from bootstrap.contexts.src_lib.module import SourceModule, build_source_module
from domain.assistant.infrastructure.adapters.in_memory_document_chunker import (
    InMemoryDocumentChunker,
)
from domain.assistant.infrastructure.adapters.in_memory_document_parser import (
    InMemoryDocumentParser,
)
from domain.assistant.infrastructure.adapters.in_memory_embedding_generator import (
    InMemoryEmbeddingGenerator,
)
from domain.assistant.infrastructure.adapters.in_memory_vector_store import (
    InMemoryVectorStore,
)
from domain.assistant.infrastructure.adapters.manuscript_content_provider import (
    ManuscriptContentProvider,
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
from domain.identity.infrastructure.adapters.argon_password_hasher import ArgonPasswordHasher
from domain.identity.infrastructure.adapters.in_memory_identity_repository import (
    InMemoryIdentityRepository,
)
from domain.identity.infrastructure.ports.identity_repository import IdentityRepository
from domain.identity.infrastructure.ports.password_hasher import PasswordHasher
from domain.manuscript.infrastructure.adapters.in_memory_manuscript_repository import (
    InMemoryManuscriptRepository,
)
from domain.manuscript.infrastructure.ports.manuscript_repository import ManuscriptRepository
from domain.project.infrastructure.adapters.in_memory_project_repository import (
    InMemoryProjectRepository,
)
from domain.project.infrastructure.ports.project_repository import ProjectRepository
from domain.revision_history.infrastructure.adapters.in_memory_revision_history_repository import (
    InMemoryRevisionHistoryRepository,
)
from domain.revision_history.infrastructure.adapters.manuscript_repository_reader import (
    ManuscriptRepositoryReader,
)
from domain.revision_history.infrastructure.adapters.manuscript_repository_writer import (
    ManuscriptRepositoryWriter,
)
from domain.revision_history.infrastructure.ports.revision_history_repository import (
    RevisionHistoryRepository,
)
from domain.src_lib.infrastructure.adapters.in_memory_source_repository import (
    InMemorySourceRepository,
)
from domain.src_lib.infrastructure.adapters.in_process_event_bus import InProcessEventBus
from domain.src_lib.infrastructure.ports.source_repository import SourceRepository

from .contexts.identity.module import IdentityModule, build_identity_module
from .contexts.manuscript.module import ManuscriptModule, build_manuscript_module
from .contexts.project.module import ProjectModule, build_project_module


@dataclass(frozen=True)
class Container:
    """Immutable composition root holding the wired module of every bounded context."""

    identity: IdentityModule
    project: ProjectModule
    manuscript: ManuscriptModule
    source: SourceModule
    assistant: AssistantModule
    revision_history: RevisionHistoryModule


def build_container(
    identity_repo: IdentityRepository | None = None,
    hasher: PasswordHasher | None = None,
    project_repo: ProjectRepository | None = None,
    manuscript_repo: ManuscriptRepository | None = None,
    source_repo: SourceRepository | None = None,
    publisher: InProcessEventBus | None = None,
    indexed_document_repo: IndexedDocumentRepository | None = None,
    index_job_queue: IndexJobQueue | None = None,
    source_content_provider: SourceContentProvider | None = None,
    document_parser: DocumentParser | None = None,
    document_chunker: DocumentChunker | None = None,
    embedding_generator: EmbeddingGenerator | None = None,
    vector_store: VectorStore | None = None,
    conversation_repo: ConversationRepository | None = None,
    chat_model: ChatModel | None = None,
    revision_history_repo: RevisionHistoryRepository | None = None,
) -> Container:
    """Build a Container, defaulting any unspecified dependency to an in-memory implementation."""
    identity_repo = identity_repo or InMemoryIdentityRepository(seed=True)
    hasher = hasher or ArgonPasswordHasher()
    project_repo = project_repo or InMemoryProjectRepository(seed=True)
    manuscript_repo = manuscript_repo or InMemoryManuscriptRepository(seed=False, template=False)
    source_repo = source_repo or InMemorySourceRepository()
    revision_history_repo = revision_history_repo or InMemoryRevisionHistoryRepository()

    # The event bus is the shared communication channel between bounded contexts.
    # It must be created before either context module so handlers can be subscribed
    # before the source context starts publishing events.
    event_bus = publisher or InProcessEventBus()

    # Default the content provider to read manuscript sections from the manuscript
    # repository so a ManuscriptSaved event triggers real ingestion by default.
    source_content_provider = source_content_provider or ManuscriptContentProvider(manuscript_repo)

    # Default ingestion adapters to in-memory implementations so the pipeline runs
    # end to end without external services. Production deployments can override
    # these with real adapters (e.g. chonkie, chromadb) via build_container kwargs.
    document_parser = document_parser or InMemoryDocumentParser()
    document_chunker = document_chunker or InMemoryDocumentChunker()
    embedding_generator = embedding_generator or InMemoryEmbeddingGenerator()
    vector_store = vector_store or InMemoryVectorStore()

    assistant = build_assistant_module(
        event_bus=event_bus,
        indexed_document_repo=indexed_document_repo,
        index_job_queue=index_job_queue,
        source_content_provider=source_content_provider,
        document_parser=document_parser,
        document_chunker=document_chunker,
        embedding_generator=embedding_generator,
        vector_store=vector_store,
        conversation_repo=conversation_repo,
        chat_model=chat_model,
    )

    return Container(
        identity=build_identity_module(identity_repo, hasher),
        project=build_project_module(project_repo),
        manuscript=build_manuscript_module(manuscript_repo, event_bus),
        source=build_source_module(source_repo, event_bus),
        assistant=assistant,
        revision_history=build_revision_history_module(
            repo=revision_history_repo,
            reader=ManuscriptRepositoryReader(manuscript_repo),
            writer=ManuscriptRepositoryWriter(manuscript_repo),
        ),
    )


def build_mongo_container(
    uri: str | None = None,
    db_name: str | None = None,
    **overrides: Any,  # noqa: ANN401
) -> Container:
    """Container whose repositories all persist to MongoDB.

    Connection settings default to MONGODB_URI / MONGODB_DB (see bootstrap.mongo).
    Anything else ``build_container`` accepts (chat model, vector store, ...) can be
    passed as a keyword override; an explicitly passed repository wins over the
    Mongo one, which keeps individual repositories swappable in tests.
    """
    from domain.assistant.infrastructure.adapters.mongodb_conversation_repository import (
        MongoConversationRepository,
    )
    from domain.assistant.infrastructure.adapters.mongodb_indexed_document_repository import (
        MongoIndexedDocumentRepository,
    )
    from domain.identity.infrastructure.adapters.mongodb_identity_repository import (
        MongoIdentityRepository,
    )
    from domain.manuscript.infrastructure.adapters.mongodb_manuscript_repository import (
        MongoManuscriptRepository,
    )
    from domain.project.infrastructure.adapters.mongodb_project_repository import (
        MongoProjectRepository,
    )
    from domain.revision_history.infrastructure.adapters.mongodb_revision_history_repository import (  # noqa: E501
        MongoRevisionHistoryRepository,
    )
    from domain.src_lib.infrastructure.adapters.mongodb_source_repository import (
        MongoSourceRepository,
    )

    from .mongo import create_database, mongo_settings

    default_uri, default_db = mongo_settings()
    uri = uri or default_uri
    db_name = db_name or default_db
    database = create_database(uri, db_name)

    repositories = {
        "identity_repo": MongoIdentityRepository(uri=uri, db_name=db_name),
        "project_repo": MongoProjectRepository(database),
        "manuscript_repo": MongoManuscriptRepository(database),
        "source_repo": MongoSourceRepository(database),
        "indexed_document_repo": MongoIndexedDocumentRepository(database),
        "conversation_repo": MongoConversationRepository(database),
        "revision_history_repo": MongoRevisionHistoryRepository(database),
    }
    return build_container(**{**repositories, **overrides})
