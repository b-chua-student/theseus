"""Unit tests for InMemoryProjectRepository and MongoProjectRepository."""

from __future__ import annotations

from typing import Any

from domain.project.infrastructure.adapters.in_memory_project_repository import (
    InMemoryProjectRepository,
)
from domain.project.infrastructure.adapters.mongodb_project_repository import (
    MongoProjectRepository,
)
from domain.project.models.aggregates import Project
from domain.project.models.entities import Member
from domain.project.models.value_objects import DisplayName, Email, ProjectName, Role


class _FakeCursor:
    """Minimal cursor supporting sort() for MongoProjectRepository tests."""

    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self._docs = docs

    def sort(self, key: str, direction: int) -> list[dict[str, Any]]:
        return sorted(self._docs, key=lambda doc: doc[key], reverse=direction < 0)


class _FakeCollection:
    """In-memory stand-in for a PyMongo Collection."""

    def __init__(self) -> None:
        self.docs: dict[str, dict[str, Any]] = {}
        self.indexes: list[str] = []

    def create_index(self, field: str) -> None:
        self.indexes.append(field)

    def insert_one(self, doc: dict[str, Any]) -> None:
        self.docs[doc["_id"]] = dict(doc)

    def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        doc = self.docs.get(query["_id"])
        return dict(doc) if doc is not None else None

    def find(self, query: dict[str, Any]) -> _FakeCursor:
        owner_id = query["owner.id"]
        matched = [dict(d) for d in self.docs.values() if d["owner"]["id"] == owner_id]
        return _FakeCursor(matched)

    def replace_one(self, query: dict[str, Any], doc: dict[str, Any]) -> None:
        if query["_id"] in self.docs:
            self.docs[query["_id"]] = dict(doc)

    def delete_one(self, query: dict[str, Any]) -> None:
        self.docs.pop(query["_id"], None)


class _FakeDatabase:
    """In-memory stand-in for a PyMongo Database."""

    def __init__(self) -> None:
        self.collections: dict[str, _FakeCollection] = {}

    def __getitem__(self, name: str) -> _FakeCollection:
        if name not in self.collections:
            self.collections[name] = _FakeCollection()
        return self.collections[name]


def _make_sample_project(name: str = "Sample Project") -> Project:
    """Create a Project aggregate with an owner and one editor member."""
    owner = Member.join(DisplayName("Owner User"), Email("owner@example.com"), Role.EDITOR)
    member = Member.join(DisplayName("Member User"), Email("member@example.com"), Role.VIEWER)
    project = Project.create(name=ProjectName(name), owner=owner, description="Desc")
    project.add_member(member)
    return project


def test_in_memory_repository_crud_and_seed() -> None:
    """Verify InMemoryProjectRepository CRUD operations and optional seeding."""
    seeded = InMemoryProjectRepository(seed=True, totalProjects=3)
    assert len(seeded._db) == 3

    repo = InMemoryProjectRepository()
    project = _make_sample_project("Alpha")
    repo.add_project(project)

    assert repo.get_project_by_id(project.id) is project
    assert repo.get_project_by_name(ProjectName("Alpha")) is project
    assert repo.get_project_by_name(ProjectName("Missing")) is None
    assert repo.get_projects_owned_by_member_id(project.owner.id) == [project]

    project.rename(ProjectName("Beta"))
    repo.update_project(project)
    assert repo.get_project_by_name(ProjectName("Beta")) is project

    repo.delete_project_by_id(project.id)
    assert repo.get_project_by_id(project.id) is None


def test_mongo_repository_crud_and_document_mapping() -> None:
    """Verify MongoProjectRepository persists, maps, queries, updates, and deletes projects."""
    db = _FakeDatabase()
    repo = MongoProjectRepository(db, collection="projects")  # type: ignore[arg-type]

    assert "owner.id" in db["projects"].indexes

    project = _make_sample_project("Mongo Project")
    repo.add_project(project)

    loaded = repo.get_project_by_id(project.id)
    assert loaded is not None
    assert loaded.id == project.id
    assert loaded.name == project.name
    assert loaded.description == "Desc"
    assert loaded.owner.email.value == "owner@example.com"
    assert len(loaded.members) == 1
    assert loaded.members[0].display_name.value == "Member User"

    owned = repo.get_projects_owned_by_member_id(project.owner.id)
    assert [p.id for p in owned] == [project.id]

    project.rename(ProjectName("Renamed Mongo Project"))
    repo.update_project(project)
    updated = repo.get_project_by_id(project.id)
    assert updated is not None
    assert updated.name.value == "Renamed Mongo Project"

    repo.delete_project_by_id(project.id)
    assert repo.get_project_by_id(project.id) is None

    # Updating a deleted project should remain a no-op
    repo.update_project(project)
    assert repo.get_project_by_id(project.id) is None
