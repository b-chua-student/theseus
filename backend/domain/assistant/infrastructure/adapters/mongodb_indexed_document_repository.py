from uuid import UUID

from pymongo.database import Database

from domain.assistant.infrastructure.ports.indexed_document_repository import (
    IndexedDocumentRepository,
)
from domain.assistant.models.aggregates import IndexedDocument
from domain.assistant.models.value_objects import (
    Chunk,
    ChunkId,
    DocumentRefId,
    IndexedDocumentId,
    IndexedDocumentTitle,
    IndexStatus,
    ProjectId,
)


class MongoIndexedDocumentRepository(IndexedDocumentRepository):
    """Indexed documents keyed by the document they index (manuscript or source).

    ``doc_ref_id`` is the natural key (one IndexedDocument per source document), so it
    is the Mongo ``_id``; the aggregate's own random id is stored alongside it.
    """

    def __init__(self, database: Database, *, collection: str = "indexed_documents") -> None:
        self._documents = database[collection]
        self._documents.create_index("project_id")

    # ---- mapping ----
    @staticmethod
    def _to_doc(document: IndexedDocument) -> dict:
        return {
            "_id": str(document.doc_ref_id.value),
            "id": str(document.id.value),
            "title": document.title.value,
            "project_id": str(document.project_id.value),
            # Stored by name rather than number so reordering the enum can't corrupt data.
            "status": document.status.name,
            "chunks": [
                {
                    "id": str(c.id.value),
                    "text": c.text,
                    "position": c.position,
                    "location": c.location,
                    "content_hash": c.content_hash,
                }
                for c in document.chunks
            ],
        }

    @staticmethod
    def _to_document(doc: dict) -> IndexedDocument:
        return IndexedDocument(
            id=IndexedDocumentId(UUID(doc["id"])),
            doc_ref_id=DocumentRefId(UUID(doc["_id"])),
            title=IndexedDocumentTitle(doc["title"]),
            project_id=ProjectId(UUID(doc["project_id"])),
            status=IndexStatus[doc["status"]],
            chunks=[
                Chunk(
                    id=ChunkId(UUID(c["id"])),
                    text=c["text"],
                    position=c["position"],
                    location=c["location"],
                    content_hash=c["content_hash"],
                )
                for c in doc["chunks"]
            ],
        )

    # ---- port implementation ----
    def add(self, document: IndexedDocument) -> None:
        self.save(document)

    def save(self, document: IndexedDocument) -> None:
        self._documents.replace_one(
            {"_id": str(document.doc_ref_id.value)}, self._to_doc(document), upsert=True
        )

    def get_by_doc_ref_id(self, doc_ref_id: DocumentRefId) -> IndexedDocument | None:
        doc = self._documents.find_one({"_id": str(doc_ref_id.value)})
        return self._to_document(doc) if doc else None

    def list_by_project(self, project_id: ProjectId) -> list[IndexedDocument]:
        docs = self._documents.find({"project_id": str(project_id.value)})
        return [self._to_document(d) for d in docs]
