from domain.assistant.infrastructure.ports.conversation_repository import ConversationRepository
from domain.assistant.models.aggregates import Conversation
from domain.assistant.models.value_objects import ConversationId, ProjectId


class InMemoryConversationRepository(ConversationRepository):
    """Dict-backed ConversationRepository; contents are lost on restart."""

    def __init__(self) -> None:
        self._db: dict[ConversationId, Conversation] = {}

    def save(self, conversation: Conversation) -> None:
        self._db[conversation.id] = conversation

    def get(self, conversation_id: ConversationId) -> Conversation | None:
        return self._db.get(conversation_id)

    def list_by_project(self, project_id: ProjectId) -> list[Conversation]:
        return sorted(
            (c for c in self._db.values() if c.project_id == project_id),
            key=lambda c: c.exchanges[-1].asked_at if c.exchanges else c.started_at,
            reverse=True,
        )
