import builtins
import logging
import re
from collections.abc import Callable
from dataclasses import replace
from typing import Literal

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
    Citation,
    ConversationId,
    DocumentRefId,
    ExchangeContext,
    ProjectId,
    Query,
    RetrievedChunk,
    SelectedSource,
)

logger = logging.getLogger(__name__)

# The model cites an excerpt by its number in square brackets, such as [1].
_CITED_KEY = re.compile(r"\[(\d+)\]")


class ChatService:
    """Starts conversations and answers questions, grounded in indexed sources.

    Source retrieval requires embedding, vector store, document repository, and
    an active source ID reader; otherwise the model gets no retrieved context.
    """

    def __init__(
        self,
        repository: ConversationRepository,
        model: ChatModel,
        embedding_generator: EmbeddingGenerator | None = None,
        vector_store: VectorStore | None = None,
        document_repository: IndexedDocumentRepository | None = None,
        top_k: int = 5,
        source_ids: Callable[[ProjectId], list[DocumentRefId]] | None = None,
    ) -> None:
        """Configure conversation storage, the chat model, and optional retrieval."""
        self._repository = repository
        self._model = model
        self._embedding_generator = embedding_generator
        self._vector_store = vector_store
        self._document_repository = document_repository
        self._top_k = top_k
        self._source_ids = source_ids

    def start(self, project_id: str) -> ConversationId:
        """Start a conversation in the given project and return its id."""
        conversation = Conversation.start(ProjectId.from_str(project_id))
        self._repository.save(conversation)
        return conversation.id

    def list(self, project_id: str) -> list[Conversation]:
        """List conversations for the given project."""
        return self._repository.list_by_project(ProjectId.from_str(project_id))

    def get(self, project_id: str, conversation_id: str) -> Conversation:
        """Return the conversation if it belongs to the given project."""
        conversation = self._repository.get(ConversationId.from_str(conversation_id))
        if conversation is None or conversation.project_id != ProjectId.from_str(project_id):
            raise ConversationNotFoundError(f"Conversation '{conversation_id}' not found")
        return conversation

    def ask(
        self,
        conversation_id: str,
        text: str,
        context_scope: Literal["none", "manuscript", "source_library"] = "source_library",
        source_ids: builtins.list[str] | None = None,
        manuscript_text: str = "",
        project_id: str | None = None,
        quote: str | None = None,
        context: ExchangeContext | None = None,
    ) -> Answer:
        """Answer ``text`` within a conversation and return the answer.

        ``context`` carries the decoded inputs. Without it, the legacy ``context_scope``,
        ``source_ids``, ``manuscript_text`` and ``quote`` arguments are decoded here.

        Raises:
            ConversationNotFoundError: If the conversation does not exist.
            ChatModelError: If the model fails; the exchange is discarded so the user can retry.
            ValueError: If ``context_scope`` is not a supported scope.
        """
        if context is None:
            context = ExchangeContext.decode(context_scope, manuscript_text, source_ids, quote)
        conversation = self._repository.get(ConversationId.from_str(conversation_id))
        if conversation is None:
            raise ConversationNotFoundError(f"Conversation '{conversation_id}' not found")

        if project_id is not None:
            self.get(project_id, conversation_id)

        query = Query(text)
        history = conversation.history
        exchange = conversation.ask(query)

        try:
            selected = list(context.source_ids) if context.source_ids is not None else None
            retrieved = (
                self._retrieve(conversation.project_id, query, selected, context.quote)
                if context.search_library
                else []
            )
            answer = self._model.reply(
                history,
                query,
                retrieved,
                manuscript_text=context.manuscript_text,
                quote=context.quote,
            )
        except ChatModelError:
            # Don't leave the exchange pending, or every later question would be rejected.
            conversation.discard_pending()
            raise
        except Exception as exc:
            conversation.discard_pending()
            logger.exception("ChatService: model failed unexpectedly")
            raise ChatModelError("The assistant failed to answer.") from exc

        answer = replace(answer, citations=self._citations(answer, retrieved))
        conversation.context_scope = context.scope
        conversation.web = context.web
        conversation.manuscript = context.manuscript
        conversation.source_ids = (
            list(context.source_ids) if context.source_ids is not None else None
        )
        conversation.sources = self._selected_sources(conversation, context.source_ids)
        conversation.answer(exchange.id, answer)

        self._repository.save(conversation)
        return answer

    @staticmethod
    def _citations(answer: Answer, excerpts: builtins.list[RetrievedChunk]) -> tuple[Citation, ...]:
        """Resolve the excerpt keys cited in ``answer`` against the excerpts supplied.

        A key that matches no supplied excerpt is discarded, so only supplied library evidence
        is cited.
        """
        resolved: builtins.list[Citation] = []
        for key in dict.fromkeys(_CITED_KEY.findall(answer.text)):
            position = int(key)
            if 1 <= position <= len(excerpts):
                chunk = excerpts[position - 1]
                resolved.append(Citation(key, chunk.doc_ref_id, chunk.title, chunk.location))
        return tuple(resolved)

    def _selected_sources(
        self, conversation: Conversation, source_ids: tuple[str, ...] | None
    ) -> builtins.list[SelectedSource]:
        """Pair each selected source ID with its title as of now.

        Titles come from the project's own documents only. A source that is no longer indexed
        keeps the title saved earlier, so it can still be named later.
        """
        if not source_ids:
            return []
        earlier = {source.id: source.title for source in conversation.sources}
        current = (
            {
                str(d.doc_ref_id.value): d.title.value
                for d in self._document_repository.list_by_project(conversation.project_id)
            }
            if self._document_repository is not None
            else {}
        )
        return [
            SelectedSource(id=value, title=current.get(value, earlier.get(value, "")))
            for value in source_ids
        ]

    def _retrieve(
        self,
        project_id: ProjectId,
        query: Query,
        source_ids: builtins.list[str] | None = None,
        quote: str | None = None,
    ) -> builtins.list[RetrievedChunk]:
        """Passages from the selected, searchable sources of the project; [] if unavailable.

        Each source is searched on its own, so a source with many matches cannot use up the
        share of another. Every passage carries its source ID and title. Passages are returned
        in rounds, best passage of each source first, and the total is capped at ``top_k``.
        """
        if (
            self._embedding_generator is None
            or self._vector_store is None
            or self._document_repository is None
            or self._source_ids is None
        ):
            return []
        try:
            allowed = set(self._source_ids(project_id))
            if source_ids is not None:
                selected = set(source_ids)
                allowed = {ref for ref in allowed if str(ref.value) in selected}
            titles = {
                d.doc_ref_id: d.title.value
                for d in self._document_repository.list_by_project(project_id)
                if d.is_searchable and d.doc_ref_id in allowed
            }
            if not titles:
                return []
            # The generator embeds chunks, so wrap the question (with the quoted claim, when
            # there is one) as a throwaway chunk.
            text = f"{quote}\n{query.text}" if quote else query.text
            probe = Chunk(id=ChunkId.new(), text=text, position="", location="", content_hash="")
            [embedding] = self._embedding_generator.generate([probe])
            vector = embedding.vector
            store = self._vector_store
        except Exception:
            # Retrieval is best-effort: an outage shouldn't block chat.
            logger.exception("ChatService: retrieval failed; answering without context")
            return []

        per_source: builtins.list[builtins.list[RetrievedChunk]] = []
        for doc_ref_id, title in titles.items():
            try:
                found = store.query(vector, k=self._top_k, doc_ref_ids=[doc_ref_id])
            except Exception:
                logger.exception("ChatService: searching source %s failed", doc_ref_id.value)
                continue
            passages = [
                replace(chunk, doc_ref_id=doc_ref_id, title=title)
                for chunk in found
                if chunk.doc_ref_id == doc_ref_id
            ]
            if passages:
                per_source.append(sorted(passages, key=lambda chunk: chunk.score, reverse=True))
        per_source.sort(key=lambda passages: passages[0].score, reverse=True)

        admitted: builtins.list[RetrievedChunk] = []
        rank = 0
        while len(admitted) < self._top_k and any(len(p) > rank for p in per_source):
            for passages in per_source:
                if len(passages) > rank and len(admitted) < self._top_k:
                    admitted.append(passages[rank])
            rank += 1
        return admitted
