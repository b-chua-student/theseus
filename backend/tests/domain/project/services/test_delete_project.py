import pytest

from domain.project.models.aggregates import Project
from domain.project.models.entities import Member
from domain.project.models.value_objects import DisplayName, Email, ProjectName
from domain.project.services.delete_project import DeleteProjectService


@pytest.fixture
def service(repository):
    return DeleteProjectService(repository)


def test_delete_project_removes_from_db(service, repository) -> None:
    project = Project.create(
        name=ProjectName("Test Project"),
        owner=Member.join(display_name=DisplayName("Test User"), email=Email("test@example.com")),
    )

    repository.add_project(project)

    assert repository.get_project_by_id(project.id) is not None

    service.execute(str(project.id.value))

    assert repository.get_project_by_id(project.id) is None
