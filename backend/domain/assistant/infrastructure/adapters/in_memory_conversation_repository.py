from domain.assistant.infrastructure.ports.conversation_repository import ConversationRepository
from domain.assistant.models.aggregates import Conversation
from domain.assistant.models.value_objects import ConversationId


class InMemoryConversationRepository(ConversationRepository):
    """Dict-backed ConversationRepository; contents are lost on restart."""

    def __init__(self) -> None:
        self._db: dict[ConversationId, Conversation] = {}

    def save(self, conversation: Conversation) -> None:
        self._db[conversation.id] = conversation

    def get(self, conversation_id: ConversationId) -> Conversation | None:
        return self._db.get(conversation_id)
