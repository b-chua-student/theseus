from uuid import uuid4

import pytest

from domain.manuscript.aggregates import Manuscript


def test_delete_manuscript(manuscript_repo, manuscript, delete_manuscript_service) -> None:
    manuscript_repo.save(manuscript)

    delete_manuscript_service.execute(manuscript.id)

    assert manuscript_repo.get_by_id(manuscript.id) is None
    assert not manuscript_repo.exists(manuscript.id)


def test_delete_manuscript_not_found(manuscript, delete_manuscript_service) -> None:
    manuscript_id = manuscript.id

    with pytest.raises(ValueError, match=f"Manuscript with ID {manuscript_id} not found"):
        delete_manuscript_service.execute(manuscript_id)


def test_delete_manuscript_preserves_other_manuscripts(
    manuscript_repo, delete_manuscript_service
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

    manuscript_repo.save(first)
    manuscript_repo.save(second)

    delete_manuscript_service.execute(first.id)

    assert manuscript_repo.get_by_id(first.id) is None
    assert manuscript_repo.get_by_id(second.id) is second


def test_delete_manuscript_twice_raises(
    manuscript_repo, manuscript, delete_manuscript_service
) -> None:
    manuscript_repo.save(manuscript)
    delete_manuscript_service.execute(manuscript.id)

    with pytest.raises(ValueError, match=f"Manuscript with ID {manuscript.id} not found"):
        delete_manuscript_service.execute(manuscript.id)


def test_delete_manuscript_allows_resave(
    manuscript_repo, manuscript, delete_manuscript_service
) -> None:
    manuscript_repo.save(manuscript)
    delete_manuscript_service.execute(manuscript.id)

    manuscript_repo.save(manuscript)

    assert manuscript_repo.exists(manuscript.id)
    assert manuscript_repo.get_by_id(manuscript.id) is manuscript


def test_delete_manuscript_does_not_affect_exists_of_others(
    manuscript_repo, delete_manuscript_service
) -> None:
    first = Manuscript(id=uuid4(), project_id=uuid4(), title="First Paper")
    second = Manuscript(id=uuid4(), project_id=uuid4(), title="Second Paper")
    manuscript_repo.save(first)
    manuscript_repo.save(second)

    delete_manuscript_service.execute(first.id)

    assert not manuscript_repo.exists(first.id)
    assert manuscript_repo.exists(second.id)


def test_delete_manuscript_same_project_preserves_siblings(
    manuscript_repo, delete_manuscript_service
) -> None:
    project_id = uuid4()
    first = Manuscript(id=uuid4(), project_id=project_id, title="First Paper")
    second = Manuscript(id=uuid4(), project_id=project_id, title="Second Paper")
    manuscript_repo.save(first)
    manuscript_repo.save(second)

    delete_manuscript_service.execute(first.id)

    assert manuscript_repo.get_by_id(second.id) is second


def test_delete_manuscript_unknown_id_leaves_repo_unchanged(
    manuscript_repo, manuscript, delete_manuscript_service
) -> None:
    manuscript_repo.save(manuscript)

    with pytest.raises(ValueError):
        delete_manuscript_service.execute(uuid4())

    assert manuscript_repo.exists(manuscript.id)
