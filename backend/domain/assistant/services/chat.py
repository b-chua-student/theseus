import logging

from domain.assistant.infrastructure.ports.chat_model import ChatModel
from domain.assistant.infrastructure.ports.conversation_repository import ConversationRepository
from domain.assistant.infrastructure.ports.embedding_generator import EmbeddingGenerator
from domain.assistant.infrastructure.ports.indexed_document_repository import (
    IndexedDocumentRepository,
)
from domain.assistant.infrastructure.ports.vector_store import VectorStore
from domain.assistant.models.aggregates import Conversation
from domain.assistant.models.errors import (
    ChatModelError,
    ConversationNotFoundError,
)
from domain.assistant.models.value_objects import (
    Answer,
    Chunk,
    ChunkId,
    ConversationId,
    ProjectId,
    Query,
    RetrievedChunk,
)

logger = logging.getLogger(__name__)


class ChatService:
    """Starts conversations and answers questions, grounded in indexed sources.

    Retrieval is enabled only when ``embedding_generator``, ``vector_store`` and
    ``document_repository`` are all supplied; otherwise the model gets no context.
    """

    def __init__(
        self,
        repository: ConversationRepository,
        model: ChatModel,
        embedding_generator: EmbeddingGenerator | None = None,
        vector_store: VectorStore | None = None,
        document_repository: IndexedDocumentRepository | None = None,
        top_k: int = 5,
    ) -> None:
        self._repository = repository
        self._model = model
        self._embedding_generator = embedding_generator
        self._vector_store = vector_store
        self._document_repository = document_repository
        self._top_k = top_k

    def start(self, project_id: str) -> ConversationId:
        """Start a conversation in the given project and return its id."""
        conversation = Conversation.start(ProjectId.from_str(project_id))
        self._repository.save(conversation)
        return conversation.id

    def ask(self, conversation_id: str, text: str) -> Answer:
        """Answer ``text`` within a conversation and return the answer.

        Raises:
            ConversationNotFoundError: If the conversation does not exist.
            ChatModelError: If the model fails; the exchange is discarded so the user can retry.
        """
        conversation = self._repository.get(ConversationId.from_str(conversation_id))
        if conversation is None:
            raise ConversationNotFoundError(f"Conversation '{conversation_id}' not found")

        query = Query(text)
        history = conversation.history
        exchange = conversation.ask(query)

        try:
            context = self._retrieve(conversation.project_id, query)
            answer = self._model.reply(history, query, context)
        except ChatModelError:
            # Don't leave the exchange pending, or every later question would be rejected.
            conversation.discard_pending()
            raise
        except Exception as exc:
            conversation.discard_pending()
            logger.exception("ChatService: model failed unexpectedly")
            raise ChatModelError("The assistant failed to answer.") from exc

        conversation.answer(exchange.id, answer)

        self._repository.save(conversation)
        return answer

    def _retrieve(self, project_id: ProjectId, query: Query) -> list[RetrievedChunk]:
        """Top-k chunks from the project's searchable documents; [] if unavailable."""
        if (
            self._embedding_generator is None
            or self._vector_store is None
            or self._document_repository is None
        ):
            return []
        try:
            doc_ref_ids = [
                d.doc_ref_id
                for d in self._document_repository.list_by_project(project_id)
                if d.is_searchable
            ]
            if not doc_ref_ids:
                return []
            # The generator embeds chunks, so wrap the question as a throwaway chunk.
            probe = Chunk(
                id=ChunkId.new(), text=query.text, position="", location="", content_hash=""
            )
            [embedding] = self._embedding_generator.generate([probe])
            return self._vector_store.query(
                embedding.vector, k=self._top_k, doc_ref_ids=doc_ref_ids
            )
        except Exception:
            # Retrieval is best-effort: a vector store outage shouldn't block chat.
            logger.exception("ChatService: retrieval failed; answering without context")
            return []
