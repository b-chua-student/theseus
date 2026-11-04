from uuid import UUID

from pymongo.database import Database

from domain.shared.clock import now
from domain.src_lib.infrastructure.ports.source_repository import SourceRepository
from domain.src_lib.models.aggregates import Source
from domain.src_lib.models.value_objects import Author, SourceId, SourceTitle


class MongoSourceRepository(SourceRepository):
    """Sources stored one per document. Removed sources are kept (soft delete)."""

    def __init__(self, database: Database, *, collection: str = "sources") -> None:
        self._sources = database[collection]
        self._sources.create_index("removed_at")

    # ---- mapping ----
    @staticmethod
    def _to_doc(source: Source) -> dict:
        return {
            "title": source.title.value,
            "authors": [a.name for a in source.authors],
            "year": source.year,
            "file_ref": source.file_ref,
            "project_id": str(source.project_id),
            "removed_at": source.removed_at,
        }

    @staticmethod
    def _to_source(doc: dict) -> Source:
        return Source(
            id=SourceId(UUID(doc["_id"])),
            title=SourceTitle(doc["title"]),
            authors=tuple(Author(name) for name in doc["authors"]),
            year=doc["year"],
            file_ref=doc["file_ref"],
            project_id=UUID(doc["project_id"]),
            removed_at=doc["removed_at"],
        )

    # ---- port implementation ----
    def get(self, source_id: SourceId) -> Source | None:
        doc = self._sources.find_one({"_id": str(source_id.value)})
        return self._to_source(doc) if doc else None

    def list_active(self) -> list[Source]:
        docs = self._sources.find({"removed_at": None}).sort("created_at", 1)
        return [self._to_source(d) for d in docs]

    def save(self, source: Source) -> None:
        self._sources.update_one(
            {"_id": str(source.id.value)},
            {"$set": self._to_doc(source), "$setOnInsert": {"created_at": now()}},
            upsert=True,
        )
