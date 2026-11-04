import pytest

from domain.project.models.value_objects import ProjectName
from domain.project.services.create_project import CreateProjectService


@pytest.fixture
def service(repository):
    return CreateProjectService(repository)


def test_create_project_persists(service, repository) -> None:
    service.execute(
        project_name="Test Project", owner_name="Test Owner", owner_email="test@email.com"
    )

    retrieved = repository.get_project_by_name(ProjectName("Test Project"))

    assert retrieved is not None
    assert retrieved.name.value == "Test Project"
    assert retrieved.owner.display_name.value == "Test Owner"
    assert retrieved.owner.email.value == "test@email.com"
