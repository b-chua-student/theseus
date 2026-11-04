from dataclasses import dataclass

import pytest

from domain.project.models.aggregates import Project
from domain.project.models.entities import Member
from domain.project.models.value_objects import DisplayName, Email, ProjectName


@pytest.fixture
def test_project():
    return TestProject()


@dataclass
class TestProject:
    name: str = "test project"
    owner: Member = Member.join(DisplayName("test member"), Email("test@email.com"))


def test_get_projects_owned_by_member_id(repository, test_project) -> None:
    for _i in range(5):
        repository.add_project(
            Project.create(
                name=test_project.name,
                owner=test_project.owner,
            )
        )

    retrieved_projects = repository.get_projects_owned_by_member_id(test_project.owner)

    for project in retrieved_projects:
        assert project.name == test_project.name
        assert project.owner == test_project.owner


def test_add_project(repository, test_project) -> None:
    project = Project.create(name=test_project.name, owner=test_project.owner)

    repository.add_project(project)

    retrieved = repository.get_project_by_id(project.id)

    assert retrieved is not None
    assert retrieved.id == project.id


def test_update_project(repository, test_project) -> None:
    project = Project.create(
        name=test_project.name,
        owner=test_project.owner,
    )

    repository.add_project(project)

    assert repository.get_project_by_id(project.id) is not None

    project.rename(ProjectName("updated project"))
    project.edit_description("new description")

    repository.update_project(project)

    retrieved = repository.get_project_by_id(project.id)

    assert retrieved is not None
    assert retrieved.id == project.id
    assert retrieved.name == ProjectName("updated project")
    assert retrieved.description == "new description"
