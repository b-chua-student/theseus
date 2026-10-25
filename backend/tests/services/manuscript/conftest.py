# conftest.py
from uuid import uuid4

import pytest

from domain.manuscript.aggregates import Manuscript
from repositories.manuscript.fake_manuscript_repository import FakeManuscriptRepository
from repositories.manuscript.manuscript_repository import ManuscriptRepository
from services.manuscript.create_manuscript import CreateManuscriptService
from services.manuscript.delete_manuscript import DeleteManuscriptService
from services.manuscript.get_all_manuscript import GetAllManuscriptService


@pytest.fixture
def manuscript_repo() -> ManuscriptRepository:
    """Provide a seeded in-memory manuscript repository.

    Returns:
        FakeManuscriptRepository: Fake repository pre-populated with seed data.
    """
    return FakeManuscriptRepository(seed=True)


@pytest.fixture
def manuscript() -> Manuscript:
    """Provide a sample manuscript.

    Returns:
        Manuscript: Manuscript with random IDs and a fixed title.
    """
    return Manuscript(id=uuid4(), project_id=uuid4(), title="My Test Book")


@pytest.fixture
def delete_manuscript_service(
    manuscript_repo: ManuscriptRepository,
) -> DeleteManuscriptService:
    """Provide the delete service wired to a repository.

    Args:
        manuscript_repo (ManuscriptRepository): Injected repository.

    Returns:
        DeleteManuscriptService: Service under test.
    """
    return DeleteManuscriptService(manuscript_repo)


@pytest.fixture
def create_manuscript_service(
    manuscript_repo: ManuscriptRepository,
) -> CreateManuscriptService:
    """Provide the create service wired to a repository.

    Args:
        manuscript_repo (ManuscriptRepository): Injected repository.

    Returns:
        CreateManuscriptService: Service under test.
    """
    return CreateManuscriptService(manuscript_repo)


@pytest.fixture
def get_all_manuscript_service(
    manuscript_repo: ManuscriptRepository,
) -> GetAllManuscriptService:
    """Provide the get-all service wired to a repository.

    Args:
        manuscript_repo (ManuscriptRepository): Injected repository.

    Returns:
        GetAllManuscriptService: Service under test.
    """
    return GetAllManuscriptService(manuscript_repo)
