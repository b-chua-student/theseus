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
from domain.assistant.infrastructure.ports.token_counter import TokenCounter
from domain.assistant.infrastructure.ports.vector_store import VectorStore
from domain.assistant.models.aggregates import Conversation
from domain.assistant.models.entities import Exchange
from domain.assistant.models.errors import (
    ChatModelError,
    ConversationNotFoundError,
)
from domain.assistant.models.value_objects import (
    Answer,
    Citation,
    ConversationId,
    DocumentRefId,
    ExchangeContext,
    ProjectId,
    Query,
    RetrievedChunk,
    SelectedSource,
)
from domain.assistant.services.evidence_retrieval import Evidence, EvidenceRetriever

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
        relevance_threshold: float | None = None,
        token_counter: TokenCounter | None = None,
        context_window: int | None = None,
        response_reserve: int = 0,
    ) -> None:
        """Configure conversation storage, the chat model, and optional retrieval.

        ``top_k`` is the most passages taken from any one source. ``relevance_threshold`` is the
        lowest cosine score a passage may have. With a ``token_counter`` and a ``context_window``,
        evidence is fitted into the window, less ``response_reserve`` tokens kept for the answer.
        """
        self._repository = repository
        self._model = model
        self._document_repository = document_repository
        self._retriever = EvidenceRetriever(
            embedding_generator,
            vector_store,
            document_repository,
            source_ids,
            passages_per_source=top_k,
            relevance_threshold=relevance_threshold,
            token_counter=token_counter,
            context_window=context_window,
            response_reserve=response_reserve,
        )

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
            evidence = (
                self._retriever.retrieve(
                    conversation.project_id,
                    query.text,
                    context.source_ids,
                    quote=context.quote,
                    draft=context.manuscript_text,
                    fixed_texts=self._fixed_texts(history, query, context),
                    known_titles={s.id: s.title for s in conversation.sources if s.title},
                )
                if context.search_library
                else Evidence.empty()
            )
            answer = self._model.reply(
                history,
                query,
                evidence.excerpts,
                manuscript_text=context.manuscript_text,
                quote=context.quote,
                outcomes=evidence.reported,
                web=context.web,
            )
        except ChatModelError:
            # Don't leave the exchange pending, or every later question would be rejected.
            conversation.discard_pending()
            raise
        except Exception as exc:
            conversation.discard_pending()
            logger.exception("ChatService: model failed unexpectedly")
            raise ChatModelError("The assistant failed to answer.") from exc

        try:
            citations = self._citations(answer, evidence.excerpts)
            report = evidence.gap_report()
            text = f"{answer.text}\n\n{report}" if report else answer.text
            answer = replace(answer, text=text, citations=citations)
            conversation.context_scope = context.scope
            conversation.web = context.web
            conversation.manuscript = context.manuscript
            conversation.source_ids = (
                list(context.source_ids) if context.source_ids is not None else None
            )
            conversation.sources = self._selected_sources(conversation, context.source_ids)
            conversation.answer(exchange.id, answer)

            self._repository.save(conversation)
        except Exception:
            # The model already answered; don't leave the exchange pending, or every later
            # question would be rejected.
            conversation.discard_pending()
            raise
        return answer

    @staticmethod
    def _fixed_texts(
        history: builtins.list[Exchange], query: Query, context: ExchangeContext
    ) -> builtins.list[str]:
        """Return the text sent to the model whatever evidence is found, for the budget."""
        texts = [query.text]
        for exchange in history:
            texts.append(exchange.query.text)
            if exchange.answer is not None:
                texts.append(exchange.answer.text)
        texts.extend(t for t in (context.manuscript_text, context.quote) if t)
        return texts

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
        current: dict[str, str] = {}
        if self._document_repository is not None:
            try:
                current = {
                    str(d.doc_ref_id.value): d.title.value
                    for d in self._document_repository.list_by_project(conversation.project_id)
                }
            except Exception:
                # A failed refresh keeps the saved titles; it must not lose the answer.
                logger.exception("ChatService: refreshing source titles failed; keeping saved ones")
        return [
            SelectedSource(id=value, title=current.get(value, earlier.get(value, "")))
            for value in source_ids
        ]
