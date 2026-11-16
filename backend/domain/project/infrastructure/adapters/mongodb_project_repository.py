from uuid import UUID

from pymongo.database import Database

from domain.project.infrastructure.ports.project_repository import ProjectRepository
from domain.project.models.aggregates import Project
from domain.project.models.entities import Member
from domain.project.models.value_objects import (
    DisplayName,
    Email,
    MemberId,
    ProjectId,
    ProjectName,
    ProjectSettings,
    Role,
)


class MongoProjectRepository(ProjectRepository):
    """Projects stored as one document each; the owner and members are embedded."""

    def __init__(self, database: Database, *, collection: str = "projects") -> None:
        self._projects = database[collection]
        self._projects.create_index("owner.id")

    # ---- mapping ----
    @staticmethod
    def _member_to_doc(member: Member) -> dict:
        return {
            "id": str(member.id.value),
            "display_name": member.display_name.value,
            "email": member.email.value,
            "role": member.role.name,
            "joined_at": member.joined_at,
        }

    @staticmethod
    def _member_from_doc(doc: dict) -> Member:
        return Member(
            id=MemberId(UUID(doc["id"])),
            display_name=DisplayName(doc["display_name"]),
            email=Email(doc["email"]),
            role=Role[doc["role"]],
            joined_at=doc["joined_at"],
        )

    @classmethod
    def _to_doc(cls, project: Project) -> dict:
        return {
            "_id": str(project.id.value),
            "name": project.name.value,
            "description": project.description,
            "settings": {"language": project.settings.language},
            "owner": cls._member_to_doc(project.owner),
            "members": [cls._member_to_doc(m) for m in project.members],
            "created_at": project.created_at,
        }

    @classmethod
    def _to_project(cls, doc: dict) -> Project:
        return Project(
            id=ProjectId(UUID(doc["_id"])),
            name=ProjectName(doc["name"]),
            owner=cls._member_from_doc(doc["owner"]),
            description=doc.get("description"),
            settings=ProjectSettings(language=doc["settings"]["language"]),
            members=[cls._member_from_doc(m) for m in doc.get("members", [])],
            created_at=doc["created_at"],
        )

    # ---- port implementation ----
    def get_projects_owned_by_member_id(self, member_id: MemberId) -> list[Project]:
        docs = self._projects.find({"owner.id": str(member_id.value)}).sort("created_at", 1)
        return [self._to_project(d) for d in docs]

    def add_project(self, project: Project) -> None:
        self._projects.insert_one(self._to_doc(project))

    def get_project_by_id(self, project_id: ProjectId) -> Project | None:
        doc = self._projects.find_one({"_id": str(project_id.value)})
        return self._to_project(doc) if doc else None

    def update_project(self, new_project: Project) -> None:
        # No upsert: updating a project that no longer exists is a no-op, as in memory.
        self._projects.replace_one({"_id": str(new_project.id.value)}, self._to_doc(new_project))

    def delete_project_by_id(self, project_id: ProjectId) -> None:
        self._projects.delete_one({"_id": str(project_id.value)})
