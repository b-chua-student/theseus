from uuid import UUID

from pymongo.database import Database

from domain.manuscript.infrastructure.ports.manuscript_repository import ManuscriptRepository
from domain.manuscript.models.aggregates import Manuscript
from domain.manuscript.models.entities import Section
from domain.manuscript.models.value_objects import (
    Heading,
    ManuscriptId,
    ManuscriptTitle,
    ProjectId,
    SectionId,
)
from domain.shared.clock import now


class MongoManuscriptRepository(ManuscriptRepository):
    """Manuscripts stored as one document each, with their sections embedded in order."""

    def __init__(self, database: Database, *, collection: str = "manuscripts") -> None:
        self._manuscripts = database[collection]
        self._manuscripts.create_index("project_id")

    # ---- mapping ----
    @staticmethod
    def _section_to_doc(section: Section) -> dict:
        return {
            "id": str(section.id.value),
            "parent_id": str(section.parent_id.value) if section.parent_id else None,
            "heading": section.heading.value,
            "ordinal": section.ordinal,
            "body": section.body,
        }

    @staticmethod
    def _section_from_doc(doc: dict) -> Section:
        return Section(
            id=SectionId(UUID(doc["id"])),
            parent_id=SectionId(UUID(doc["parent_id"])) if doc["parent_id"] else None,
            heading=Heading(doc["heading"]),
            ordinal=doc["ordinal"],
            body=doc["body"],
        )

    @classmethod
    def _to_manuscript(cls, doc: dict) -> Manuscript:
        return Manuscript(
            id=ManuscriptId(UUID(doc["_id"])),
            project_id=ProjectId(UUID(doc["project_id"])),
            title=ManuscriptTitle(doc["title"]),
            sections=[cls._section_from_doc(s) for s in doc["sections"]],
        )

    # ---- port implementation ----
    def save(self, manuscript: Manuscript) -> None:
        # created_at is set once, on insert, and only used to keep listings in creation order.
        self._manuscripts.update_one(
            {"_id": str(manuscript.id.value)},
            {
                "$set": {
                    "project_id": str(manuscript.project_id.value),
                    "title": manuscript.title.value,
                    "sections": [self._section_to_doc(s) for s in manuscript.sections],
                },
                "$setOnInsert": {"created_at": now()},
            },
            upsert=True,
        )

    def get_by_id(self, manuscript_id: ManuscriptId) -> Manuscript | None:
        doc = self._manuscripts.find_one({"_id": str(manuscript_id.value)})
        return self._to_manuscript(doc) if doc else None

    def get_all(self) -> list[Manuscript]:
        return [self._to_manuscript(d) for d in self._manuscripts.find().sort("created_at", 1)]

    def list_by_project_id(self, project_id: ProjectId) -> list[Manuscript]:
        docs = self._manuscripts.find({"project_id": str(project_id.value)}).sort("created_at", 1)
        return [self._to_manuscript(d) for d in docs]

    def delete(self, manuscript_id: ManuscriptId) -> None:
        self._manuscripts.delete_one({"_id": str(manuscript_id.value)})

    def exists(self, manuscript_id: ManuscriptId) -> bool:
        return self._manuscripts.count_documents({"_id": str(manuscript_id.value)}, limit=1) > 0

    def clear(self) -> None:
        self._manuscripts.delete_many({})
