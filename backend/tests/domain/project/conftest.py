import pytest

from domain.project.infrastructure.adapters.in_memory_project_repository import (
    InMemoryProjectRepository,
)


@pytest.fixture
def repository():
    return InMemoryProjectRepository()
