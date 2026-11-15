from abc import ABC, abstractmethod

from domain.assistant.models.aggregates import Conversation
from domain.assistant.models.value_objects import ConversationId


class ConversationRepository(ABC):
    """Port for persisting and retrieving Conversation aggregates."""

    @abstractmethod
    def save(self, conversation: Conversation) -> None:
        """Persist the conversation, replacing any stored one with the same id."""

    @abstractmethod
    def get(self, conversation_id: ConversationId) -> Conversation | None:
        """Return the conversation with the given id, or None if it does not exist."""
