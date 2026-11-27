import builtins
import logging
import re
import time
from collections.abc import Callable, Collection
from dataclasses import replace
from typing import Literal

from domain.assistant.infrastructure.ports.answer_validator import AnswerProposer, AnswerValidator
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
    AnswerValidationError,
    ChatModelError,
    ConversationNotFoundError,
    PromptInjectionError,
    RetrievalError,
)
from domain.assistant.models.value_objects import (
    Answer,
    ConversationId,
    DocumentRefId,
    Evidence,
    ExchangeContext,
    ProjectId,
    Query,
    SelectedSource,
)
from domain.assistant.services.answer_validation import INTERRUPTED_MESSAGE, ValidateAnswer
from domain.assistant.services.evidence_retrieval import Evidence as RetrievedEvidence
from domain.assistant.services.evidence_retrieval import EvidenceRetriever
from domain.assistant.services.evidence_retriever import EvidenceRetriever as ValidationRetriever
from domain.assistant.services.reviewed_answer_cache import (
    Recovery,
    ReviewedAnswer,
    ReviewedAnswerCache,
    evidence_key,
    fingerprint,
)

logger = logging.getLogger(__name__)

_HISTORY_LIMIT = 10

# Match requests directed at the assistant, including polite requests, at sentence starts.
_DIRECT_INSTRUCTION_REQUEST = re.compile(
    r"(?:^|[.!?]\s+|\n)\s*(?:(?:can|could|would)\s+you\s+)?(?:please[,\s]+)?"
    r"(?:"
    r"(?:ignore|disregard|override)\s+(?:all\s+)?(?:your\s+|the\s+)?"
    r"(?:previous|prior|earlier|system|internal|original)\s+(?:instructions|rules)"
    r"|(?:reveal|show|print|repeat|disclose)\s+(?:me\s+)?(?:your|the)\s+"
    r"(?:internal\s+|hidden\s+)?(?:system\s+(?:prompt|instructions)|internal instructions)"
    r")\b",
    re.IGNORECASE,
)


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
        validator: AnswerValidator | None = None,
        clock: Callable[[], float] | None = None,
        *,
        require_source_review: bool = False,
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

        self._validation_retriever = ValidationRetriever(
            embedding_generator, vector_store, document_repository, source_ids, top_k
        )
        self._top_k = top_k
        self._reviewed_cache = ReviewedAnswerCache()
        self._proposer = validator if isinstance(validator, AnswerProposer) else None
        self._review_sources = require_source_review or self._proposer is not None
        self._validate_answer = (
            ValidateAnswer(validator, self._validation_retriever, clock or time.monotonic)
            if validator is not None or self._review_sources
            else None
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
        on_draft_ready: Callable[[], None] | None = None,
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
        if _DIRECT_INSTRUCTION_REQUEST.search(query.text):
            raise PromptInjectionError(
                "Requests to override or disclose internal instructions are blocked."
            )
        history = conversation.history[-_HISTORY_LIMIT:]
        exchange = conversation.ask(query)

        cache_write: tuple[str, ReviewedAnswer] | None = None
        try:
            if context.search_library and self._validate_answer is None:
                raise AnswerValidationError(INTERRUPTED_MESSAGE)
            fixed_texts = self._fixed_texts(history, query, context)
            evidence = (
                self._retriever.retrieve(
                    conversation.project_id,
                    query.text,
                    context.source_ids,
                    quote=context.quote,
                    draft=context.manuscript_text,
                    fixed_texts=fixed_texts,
                    strict=True,
                    known_titles={s.id: s.title for s in conversation.sources if s.title},
                )
                if context.search_library
                else RetrievedEvidence.empty()
            )
            if context.search_library and self._review_sources:
                answer, cache_write = self._source_answer(
                    conversation, query, text, context, evidence, fixed_texts, on_draft_ready
                )
            else:
                answer = self._model.reply(
                    history,
                    query,
                    evidence.excerpts,
                    manuscript_text=context.manuscript_text,
                    quote=context.quote,
                    outcomes=evidence.reported,
                    web=context.web,
                )
                if context.search_library and self._validate_answer is not None:
                    if on_draft_ready is not None:
                        on_draft_ready()
                    answer = self._validate_answer.execute(
                        question=query,
                        draft=answer,
                        evidence=Evidence(tuple(evidence.excerpts)),
                        project_id=conversation.project_id,
                        source_ids=list(context.source_ids)
                        if context.source_ids is not None
                        else None,
                        manuscript_text=context.manuscript_text or "",
                    )
                else:
                    answer = replace(answer, citations=())
        except RetrievalError as exc:
            conversation.discard_pending()
            raise AnswerValidationError(INTERRUPTED_MESSAGE) from exc
        except ChatModelError:
            # Don't leave the exchange pending, or every later question would be rejected.
            conversation.discard_pending()
            raise
        except Exception as exc:
            conversation.discard_pending()
            logger.exception("ChatService: model failed unexpectedly")
            raise ChatModelError("The assistant failed to answer.") from exc

        try:
            report = evidence.gap_report(include_reported=self._review_sources)
            text = f"{answer.text}\n\n{report}" if report else answer.text
            answer = replace(answer, text=text)
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
        if cache_write is not None:
            self._reviewed_cache.put(*cache_write)
        return answer

    def _source_answer(  # noqa: PLR0913
        self,
        conversation: Conversation,
        query: Query,
        exact_question: str,
        context: ExchangeContext,
        retrieved: RetrievedEvidence,
        fixed_texts: builtins.list[str],
        on_draft_ready: Callable[[], None] | None,
    ) -> tuple[Answer, tuple[str, ReviewedAnswer] | None]:
        evidence = Evidence(tuple(retrieved.excerpts))
        if not evidence.passages:
            return Answer("The search found insufficient evidence in your selected sources."), None

        source_ids = list(context.source_ids) if context.source_ids is not None else None
        manuscript = context.manuscript_text or ""
        key = fingerprint(
            str(conversation.project_id.value),
            str(conversation.id.value),
            exact_question,
            sorted(set(source_ids)) if source_ids is not None else None,
            retrieved.searchable_scope,
            evidence_key(evidence),
            context.manuscript_text,
            context.quote,
            context.web,
            [outcome.record() for outcome in retrieved.reported],
        )

        def recover(current: Evidence, hint: str, keep: Collection[int]) -> Evidence:
            # Keep the original excerpt keys and admit new passages within the same window.
            found = self._retriever.retrieve(
                conversation.project_id,
                f"{query.text}\n{hint}",
                retrieved.searchable_scope,
                quote=context.quote,
                draft=context.manuscript_text,
                fixed_texts=fixed_texts,
                strict=True,
            )
            merged = current.merge(found.excerpts, max(self._top_k, len(current.passages)), keep)
            return merged if self._retriever.fits(merged.passages, fixed_texts) else current

        cached = self._reviewed_cache.get(key)
        if cached is not None:
            replay = evidence
            for step in cached.recovery:
                replay = recover(replay, step.query, step.keep)
                if evidence_key(replay) != step.evidence_key:
                    break
            else:
                return cached.answer, None

        proposer = self._proposer
        validator = self._validate_answer
        if proposer is None or validator is None:
            raise AnswerValidationError(INTERRUPTED_MESSAGE)
        try:
            draft = proposer.draft(query.text, evidence, manuscript, quote=context.quote)
        except ChatModelError as exc:
            raise AnswerValidationError(INTERRUPTED_MESSAGE) from exc
        recovery: list[Recovery] = []
        answer, complete = validator.review_draft(
            query,
            draft,
            evidence,
            conversation.project_id,
            source_ids,
            manuscript,
            recovery,
            on_draft_ready,
            recover=recover,
            quote=context.quote,
        )
        return answer, (key, ReviewedAnswer(answer, tuple(recovery))) if complete else None

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
