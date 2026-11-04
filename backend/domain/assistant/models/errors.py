from __future__ import annotations

from typing import TYPE_CHECKING

from domain.shared.errors import DomainError

if TYPE_CHECKING:
    from domain.assistant.models.value_objects import IndexStatus


class AssistantError(DomainError):
    """Base class for errors raised by the assistant context."""

    code = "assistant.error"


class InvalidIndexedDocumentIdError(AssistantError):
    """Raised when an IndexedDocumentId is not a UUID."""

    code = "assistant.invalid_indexed_document_id"


class InvalidProjectIdError(AssistantError):
    """Raised when a ProjectId is not a valid UUID."""

    code = "assistant.invalid_project_id_id"


class InvalidDocumentRefIdError(AssistantError):
    """Raised when a DocumentRefId is not a valid UUID."""

    code = "assistant.invalid_document_ref_id"


class InvalidIndexTransitionError(AssistantError):
    """Raised when an indexing status change is not allowed from the current status."""

    code = "indexing.invalid_transition"

    def __init__(self, current: IndexStatus, target: IndexStatus) -> None:
        self.current = current
        self.target = target
        super().__init__(
            f"Cannot transition index from '{current.value}' to '{target.value}'.",
            details={"current": current.value, "target": target.value},
        )


class EmptyChunksError(AssistantError):
    """Raised when indexing is completed with no chunks."""

    code = "assistant.empty_chunks"


class ConversationNotFoundError(AssistantError):
    """Raised when a conversation does not exist."""

    code = "assistant.conversation_not_found"


class InvalidConversationIdError(AssistantError):
    """Raised when a ConversationId is not a valid UUID."""

    code = "assistant.invalid_conversation_id"


class InvalidExchangeIdError(AssistantError):
    """Raised when an ExchangeId is not a UUID."""

    code = "assistant.invalid_exchange_id"


class EmptyQueryError(AssistantError):
    """Raised when a query is blank."""

    code = "assistant.empty_query"


class EmptyAnswerError(AssistantError):
    """Raised when an answer is blank."""

    code = "assistant.empty_answer"


class PendingExchangeError(AssistantError):
    """Raised when asking while the previous exchange is still unanswered."""

    code = "assistant.pending_exchange"


class ExchangeNotFoundError(AssistantError):
    """Raised when a conversation has no exchange with the given id."""

    code = "assistant.exchange_not_found"


class ExchangeAlreadyAnsweredError(AssistantError):
    """Raised when responding to an exchange that already has an answer."""

    code = "assistant.exchange_already_answered"


class ChatModelError(AssistantError):
    """The AI provider failed to produce an answer (outage, bad/empty/blocked response, timeout)."""

    code = "assistant.model_error"


class ChatModelRateLimitedError(ChatModelError):
    """The AI provider rejected the request because of rate limiting."""

    code = "assistant.model_rate_limited"


class ChatUnavailableError(AssistantError):
    """No chat provider is configured, so the assistant cannot answer."""

    code = "assistant.unavailable"
