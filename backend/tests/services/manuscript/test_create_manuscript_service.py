from unittest.mock import create_autospec
from uuid import UUID, uuid4

import pytest

from domain.manuscript.aggregates import Manuscript
from repositories.manuscript.manuscript_repository import ManuscriptRepository
from services.manuscript.create_manuscript import CreateManuscriptService


def test_execute_returns_manuscript_with_given_values(
    create_manuscript_service: CreateManuscriptService,
) -> None:
    project_id = uuid4()

    result = create_manuscript_service.execute(project_id=project_id, title="My Book")

    assert isinstance(result, Manuscript)
    assert isinstance(result.id, UUID)
    assert result.project_id == project_id
    assert result.title == "My Book"


def test_execute_saves_manuscript_once() -> None:
    repo = create_autospec(ManuscriptRepository, instance=True)
    service = CreateManuscriptService(repo)

    result = service.execute(project_id=uuid4(), title="My Book")

    repo.save.assert_called_once_with(result)


def test_execute_generates_unique_ids(
    create_manuscript_service: CreateManuscriptService,
) -> None:
    project_id = uuid4()

    first = create_manuscript_service.execute(project_id=project_id, title="One")
    second = create_manuscript_service.execute(project_id=project_id, title="Two")

    assert first.id != second.id


@pytest.mark.parametrize("title", ["", "   ", "\t\n"])
def test_execute_raises_value_error_for_blank_title(title: str) -> None:
    repo = create_autospec(ManuscriptRepository, instance=True)
    service = CreateManuscriptService(repo)

    with pytest.raises(ValueError):
        service.execute(project_id=uuid4(), title=title)

    repo.save.assert_not_called()
