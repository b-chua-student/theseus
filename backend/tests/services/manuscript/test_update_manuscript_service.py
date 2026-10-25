from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from services.manuscript.update_manuscript import UpdateManuscriptService


def test_execute_renames_manuscript(update_manuscript_service, manuscript_repo, manuscript) -> None:
    manuscript_repo.save(manuscript)

    result = update_manuscript_service.execute(manuscript.id, "New Title")

    assert result.id == manuscript.id
    assert result.title == "New Title"


def test_execute_persists_change(update_manuscript_service, manuscript_repo, manuscript) -> None:
    manuscript_repo.save(manuscript)

    update_manuscript_service.execute(manuscript.id, "Persisted")

    assert manuscript_repo.get_by_id(manuscript.id).title == "Persisted"


def test_execute_unknown_id_raises_value_error(update_manuscript_service) -> None:
    missing_id = uuid4()

    with pytest.raises(ValueError, match=str(missing_id)):
        update_manuscript_service.execute(missing_id, "Title")


@pytest.mark.parametrize("bad_title", ["", "   "])
def test_execute_invalid_title_raises_and_does_not_persist(
    update_manuscript_service, manuscript_repo, manuscript, bad_title
) -> None:
    manuscript_repo.save(manuscript)

    with pytest.raises(ValueError):
        update_manuscript_service.execute(manuscript.id, bad_title)

    assert manuscript_repo.get_by_id(manuscript.id).title == "My Test Book"


def test_execute_calls_save_once_with_updated_manuscript(manuscript) -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = manuscript
    service = UpdateManuscriptService(repo)

    service.execute(manuscript.id, "Mocked")

    repo.get_by_id.assert_called_once_with(manuscript.id)
    repo.save.assert_called_once_with(manuscript)


def test_execute_unknown_id_does_not_save() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None
    service = UpdateManuscriptService(repo)

    with pytest.raises(ValueError):
        service.execute(uuid4(), "Title")

    repo.save.assert_not_called()
