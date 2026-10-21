from uuid import uuid4

import pytest

from domain.manuscript.aggregates import Manuscript
from repositories.manuscript.fake_manuscript_repository import (
    FakeManuscriptRepository,
)
from services.manuscript.get_manuscript import GetManuscriptService


@pytest.fixture
def repository() -> FakeManuscriptRepository:
    return FakeManuscriptRepository()


@pytest.fixture
def service(
    repository: FakeManuscriptRepository,
) -> GetManuscriptService:
    return GetManuscriptService(repository)


@pytest.fixture
def manuscript() -> Manuscript:
    return Manuscript(
        id=uuid4(),
        project_id=uuid4(),
        title="Research Paper",
    )


def test_get_manuscript_returns_saved_manuscript(
    repository: FakeManuscriptRepository,
    service: GetManuscriptService,
    manuscript: Manuscript,
) -> None:
    repository.save(manuscript)

    result = service.execute(manuscript.id)

    assert result is manuscript
    assert result.id == manuscript.id
    assert result.project_id == manuscript.project_id
    assert result.title == "Research Paper"


def test_get_manuscript_raises_when_not_found(
    service: GetManuscriptService,
) -> None:
    with pytest.raises(ValueError, match="Manuscript not found"):
        service.execute(uuid4())


def test_get_manuscript_returns_correct_manuscript(
    repository: FakeManuscriptRepository,
    service: GetManuscriptService,
) -> None:
    first = Manuscript(
        id=uuid4(),
        project_id=uuid4(),
        title="First Paper",
    )
    second = Manuscript(
        id=uuid4(),
        project_id=uuid4(),
        title="Second Paper",
    )

    repository.save(first)
    repository.save(second)

    result = service.execute(second.id)

    assert result.id == second.id
    assert result.title == "Second Paper"
