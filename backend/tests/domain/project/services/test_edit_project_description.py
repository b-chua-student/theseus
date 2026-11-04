import pytest

from domain.project.models.aggregates import Project
from domain.project.models.entities import Member
from domain.project.models.value_objects import DisplayName, Email, ProjectName
from domain.project.services.edit_project_description import EditProjectDescriptionService


@pytest.fixture
def service(repository):
    return EditProjectDescriptionService(repository)


def test_editing_description_persists(service, repository) -> None:
    project = Project.create(
        name=ProjectName("Test Project"),
        owner=Member.join(display_name=DisplayName("Test User"), email=Email("test@example.com")),
    )

    repository.add_project(project)

    assert repository.get_project_by_id(project.id) is not None

    service.execute(str(project.id.value), "new description")

    retrieved = repository.get_project_by_id(project.id)

    assert retrieved is not None
    assert retrieved.description == "new description"
