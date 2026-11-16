from uuid import UUID

from pymongo.database import Database

from domain.assistant.infrastructure.ports.conversation_repository import ConversationRepository
from domain.assistant.models.aggregates import Conversation
from domain.assistant.models.entities import Exchange
from domain.assistant.models.value_objects import (
    Answer,
    ConversationId,
    ExchangeId,
    ProjectId,
    Query,
)


class MongoConversationRepository(ConversationRepository):
    """Conversations stored as one document each, with exchanges embedded in order."""

    def __init__(self, database: Database, *, collection: str = "conversations") -> None:
        self._conversations = database[collection]

    # ---- mapping ----
    @staticmethod
    def _exchange_to_doc(exchange: Exchange) -> dict:
        return {
            "id": str(exchange.id.value),
            "query": exchange.query.text,
            "answer": exchange.answer.text if exchange.answer else None,
            "asked_at": exchange.asked_at,
        }

    @staticmethod
    def _exchange_from_doc(doc: dict) -> Exchange:
        return Exchange(
            id=ExchangeId(UUID(doc["id"])),
            query=Query(doc["query"]),
            answer=Answer(doc["answer"]) if doc["answer"] is not None else None,
            asked_at=doc["asked_at"],
        )

    @classmethod
    def _to_doc(cls, conversation: Conversation) -> dict:
        return {
            "_id": str(conversation.id.value),
            "project_id": str(conversation.project_id.value),
            "exchanges": [cls._exchange_to_doc(e) for e in conversation.exchanges],
            "started_at": conversation.started_at,
            "context_scope": conversation.context_scope,
            "source_ids": conversation.source_ids,
            "updated_at": conversation.exchanges[-1].asked_at
            if conversation.exchanges
            else conversation.started_at,
        }

    @classmethod
    def _to_conversation(cls, doc: dict) -> Conversation:
        return Conversation(
            id=ConversationId(UUID(doc["_id"])),
            project_id=ProjectId(UUID(doc["project_id"])),
            exchanges=[cls._exchange_from_doc(e) for e in doc["exchanges"]],
            started_at=doc["started_at"],
            context_scope=doc.get("context_scope", "source_library"),
            source_ids=doc.get("source_ids"),
        )

    # ---- port implementation ----
    def save(self, conversation: Conversation) -> None:
        self._conversations.replace_one(
            {"_id": str(conversation.id.value)}, self._to_doc(conversation), upsert=True
        )

    def get(self, conversation_id: ConversationId) -> Conversation | None:
        doc = self._conversations.find_one({"_id": str(conversation_id.value)})
        return self._to_conversation(doc) if doc else None

    def list_by_project(self, project_id: ProjectId) -> list[Conversation]:
        return [
            self._to_conversation(doc)
            for doc in self._conversations.find({"project_id": str(project_id.value)}).sort(
                [("updated_at", -1), ("started_at", -1)]
            )
        ]
