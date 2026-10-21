from uuid import uuid4

import pytest

from domain.manuscript.aggregates import Manuscript
from repositories.manuscript.fake_manuscript_repository import (
    FakeManuscriptRepository,
)
from services.manuscript.update_manuscript import UpdateManuscriptService


@pytest.fixture
def repository() -> FakeManuscriptRepository:
    return FakeManuscriptRepository()


@pytest.fixture
def service(
    repository: FakeManuscriptRepository,
) -> UpdateManuscriptService:
    return UpdateManuscriptService(repository)


@pytest.fixture
def manuscript() -> Manuscript:
    return Manuscript(
        id=uuid4(),
        project_id=uuid4(),
        title="Original Title",
    )


def test_update_manuscript_title(
    repository: FakeManuscriptRepository,
    service: UpdateManuscriptService,
    manuscript: Manuscript,
) -> None:
    repository.save(manuscript)

    result = service.execute(
        manuscript_id=manuscript.id,
        title="Updated Title",
    )

    assert result.title == "Updated Title"
    assert repository.get_by_id(manuscript.id).title == "Updated Title"


def test_update_manuscript_not_found(
    service: UpdateManuscriptService,
) -> None:
    with pytest.raises(ValueError, match="Manuscript not found"):
        service.execute(
            manuscript_id=uuid4(),
            title="Updated Title",
        )


def test_update_manuscript_empty_title_fails(
    repository: FakeManuscriptRepository,
    service: UpdateManuscriptService,
    manuscript: Manuscript,
) -> None:
    repository.save(manuscript)

    with pytest.raises(ValueError, match="title"):
        service.execute(
            manuscript_id=manuscript.id,
            title="   ",
        )

    assert repository.get_by_id(manuscript.id).title == "Original Title"
