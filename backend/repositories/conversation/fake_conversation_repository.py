from uuid import UUID

from domain.conversation.aggregates import Conversation
from domain.conversation.value_objects import ConversationId
from repositories.conversation.conversation_repository import ConversationRepository


class FakeConversationRepository(ConversationRepository):
    """In-memory conversation repository for development and testing."""

    def __init__(self) -> None:
        self._conversations: dict[ConversationId, Conversation] = {}

    def save(self, conversation: Conversation) -> None:
        self._conversations[conversation.conversation_id] = conversation

    def get_by_id(self, conversation_id: ConversationId) -> Conversation | None:
        return self._conversations.get(conversation_id)

    def get_by_manuscript_id(self, manuscript_id: UUID) -> Conversation | None:
        for conversation in self._conversations.values():
            if conversation.manuscript_id == manuscript_id:
                return conversation
        return None

    def delete(self, conversation_id: ConversationId) -> None:
        self._conversations.pop(conversation_id, None)
