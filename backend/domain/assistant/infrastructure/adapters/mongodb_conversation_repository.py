from uuid import UUID

from pymongo.database import Database

from domain.assistant.infrastructure.ports.conversation_repository import ConversationRepository
from domain.assistant.models.aggregates import Conversation
from domain.assistant.models.entities import Exchange
from domain.assistant.models.value_objects import (
    Answer,
    ChunkId,
    Citation,
    ConversationId,
    DocumentRefId,
    ExchangeId,
    ProjectId,
    Query,
)


class MongoConversationRepository(ConversationRepository):
    """Conversations stored as one document each, with exchanges embedded in order."""

    def __init__(self, database: Database, *, collection: str = "conversations") -> None:
        """Select the MongoDB collection for conversations."""
        self._conversations = database[collection]

    # ---- mapping ----
    @staticmethod
    def _exchange_to_doc(exchange: Exchange) -> dict:
        return {
            "id": str(exchange.id.value),
            "query": exchange.query.text,
            "answer": exchange.answer.text if exchange.answer else None,
            "citations": [
                {
                    "key": c.key,
                    "chunk_id": str(c.chunk_id.value),
                    "doc_ref_id": str(c.doc_ref_id.value),
                    "location": c.location,
                }
                for c in (exchange.answer.citations if exchange.answer else ())
            ],
            "asked_at": exchange.asked_at,
        }

    @staticmethod
    def _answer_from_doc(doc: dict) -> Answer | None:
        if doc["answer"] is None:
            return None
        # Exchanges stored before citations existed have no "citations" field.
        citations = tuple(
            Citation(
                key=c["key"],
                chunk_id=ChunkId(UUID(c["chunk_id"])),
                doc_ref_id=DocumentRefId(UUID(c["doc_ref_id"])),
                location=c["location"],
            )
            for c in doc.get("citations", [])
        )
        return Answer(doc["answer"], citations=citations)

    @classmethod
    def _exchange_from_doc(cls, doc: dict) -> Exchange:
        return Exchange(
            id=ExchangeId(UUID(doc["id"])),
            query=Query(doc["query"]),
            answer=cls._answer_from_doc(doc),
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
        """Insert or replace the conversation document by ID."""
        self._conversations.replace_one(
            {"_id": str(conversation.id.value)}, self._to_doc(conversation), upsert=True
        )

    def get(self, conversation_id: ConversationId) -> Conversation | None:
        """Load the conversation with the given ID, if present."""
        doc = self._conversations.find_one({"_id": str(conversation_id.value)})
        return self._to_conversation(doc) if doc else None

    def list_by_project(self, project_id: ProjectId) -> list[Conversation]:
        """List project conversations by most recent activity, then start time."""
        return [
            self._to_conversation(doc)
            for doc in self._conversations.find({"project_id": str(project_id.value)}).sort(
                [("updated_at", -1), ("started_at", -1)]
            )
        ]
