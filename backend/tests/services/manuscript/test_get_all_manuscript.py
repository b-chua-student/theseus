from unittest.mock import create_autospec

from domain.manuscript.aggregates import Manuscript
from repositories.manuscript.fake_manuscript_repository import (
    FakeManuscriptRepository,
)
from repositories.manuscript.manuscript_repository import ManuscriptRepository
from services.manuscript.get_all_manuscript import GetAllManuscriptService


def test_execute_returns_all_seeded_manuscripts(
    get_all_manuscript_service: GetAllManuscriptService,
    manuscript_repo: ManuscriptRepository,
) -> None:
    result = get_all_manuscript_service.execute()

    assert result == manuscript_repo.get_all()
    assert len(result) > 0


def test_execute_returns_empty_list_when_repository_empty() -> None:
    service = GetAllManuscriptService(FakeManuscriptRepository(seed=False))

    assert service.execute() == []


def test_execute_delegates_to_repository(manuscript: Manuscript) -> None:
    repo = create_autospec(ManuscriptRepository, instance=True)
    repo.get_all.return_value = [manuscript]
    service = GetAllManuscriptService(repo)

    result = service.execute()

    assert result == [manuscript]
    repo.get_all.assert_called_once_with()
