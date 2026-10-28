from abc import ABC, abstractmethod
from uuid import UUID

from domain.conversation.aggregates import Conversation


class ConversationRepository(ABC):
    @abstractmethod
    def get_by_manuscript_id(self, manuscript_id: UUID) -> Conversation:
        pass
