from uuid import uuid4

import pytest

from domain.revision_history.aggregates import RevisionHistory
from domain.revision_history.value_objects import CommitMessage, Snapshot
from repositories.revision_history.fake_revision_history_repository import (
    FakeRevisionHistoryRepository,
)
from services.revision_history.list_branches import ListBranchesService


@pytest.fixture
def repository() -> FakeRevisionHistoryRepository:
    return FakeRevisionHistoryRepository()


@pytest.fixture
def revision_history() -> RevisionHistory:
    history = RevisionHistory(
        project_id=uuid4(),
        manuscript_id=uuid4(),
    )
    history.initialize(
        snapshot=Snapshot("Initial manuscript content"),
        message=CommitMessage("Initial revision"),
    )
    return history


@pytest.fixture
def service(
    repository: FakeRevisionHistoryRepository,
) -> ListBranchesService:
    return ListBranchesService(repository)


@pytest.fixture
def saved_history(
    repository: FakeRevisionHistoryRepository,
    revision_history: RevisionHistory,
) -> RevisionHistory:
    repository.save(revision_history)
    return revision_history


def test_list_branches_returns_main(
    service: ListBranchesService,
    saved_history: RevisionHistory,
) -> None:
    branches = service.execute(saved_history.manuscript_id)

    assert len(branches) == 1
    assert branches[0].name == "main"


def test_list_branches_returns_all_branches(
    service: ListBranchesService,
    saved_history: RevisionHistory,
) -> None:
    saved_history.create_branch("feature")
    saved_history.create_branch("experiment")

    branches = service.execute(saved_history.manuscript_id)
    names = {branch.name for branch in branches}

    assert names == {"main", "feature", "experiment"}


def test_list_branches_for_missing_history_fails(
    service: ListBranchesService,
) -> None:
    with pytest.raises(ValueError, match="Revision history not found"):
        service.execute(uuid4())
