from uuid import uuid4

import pytest

from domain.manuscript.aggregates import Manuscript
from repositories.manuscript.fake_manuscript_repository import (
    FakeManuscriptRepository,
)
from services.manuscript.delete_manuscript import DeleteManuscriptService


@pytest.fixture
def repository() -> FakeManuscriptRepository:
    return FakeManuscriptRepository()


@pytest.fixture
def service(
    repository: FakeManuscriptRepository,
) -> DeleteManuscriptService:
    return DeleteManuscriptService(repository)


@pytest.fixture
def manuscript() -> Manuscript:
    return Manuscript(
        id=uuid4(),
        project_id=uuid4(),
        title="Research Paper",
    )


def test_delete_manuscript(
    repository: FakeManuscriptRepository,
    service: DeleteManuscriptService,
    manuscript: Manuscript,
) -> None:
    repository.save(manuscript)

    service.execute(manuscript.id)

    assert repository.get_by_id(manuscript.id) is None
    assert not repository.exists(manuscript.id)


def test_delete_manuscript_not_found(
    service: DeleteManuscriptService,
) -> None:
    with pytest.raises(ValueError, match="Manuscript not found"):
        service.execute(uuid4())


def test_delete_manuscript_preserves_other_manuscripts(
    repository: FakeManuscriptRepository,
    service: DeleteManuscriptService,
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

    service.execute(first.id)

    assert repository.get_by_id(first.id) is None
    assert repository.get_by_id(second.id) is second
