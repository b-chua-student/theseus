from abc import ABC, abstractmethod
from uuid import UUID

from domain.conversation.aggregates import Conversation
from domain.conversation.value_objects import ConversationId


class ConversationRepository(ABC):
    """Repository interface for conversations."""

    @abstractmethod
    def save(self, conversation: Conversation) -> None:
        """Persist a conversation, creating or replacing it."""

    @abstractmethod
    def get_by_id(self, conversation_id: ConversationId) -> Conversation | None:
        """Retrieve a conversation by id, or None if not found."""

    @abstractmethod
    def get_by_manuscript_id(self, manuscript_id: UUID) -> Conversation | None:
        """Retrieve the conversation for a manuscript, or None if not found."""

    @abstractmethod
    def delete(self, conversation_id: ConversationId) -> None:
        """Delete a conversation. Does nothing if it does not exist."""
