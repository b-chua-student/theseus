from uuid import uuid4

import pytest

from domain.revision_history.aggregates import RevisionHistory
from domain.revision_history.exceptions import BranchNotFoundError
from domain.revision_history.value_objects import CommitMessage, Snapshot
from repositories.revision_history.fake_revision_history_repository import (
    FakeRevisionHistoryRepository,
)
from services.revision_history.get_branch import GetBranchService


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
) -> GetBranchService:
    return GetBranchService(repository)


@pytest.fixture
def saved_history(
    repository: FakeRevisionHistoryRepository,
    revision_history: RevisionHistory,
) -> RevisionHistory:
    repository.save(revision_history)
    return revision_history


def test_get_branch(
    service: GetBranchService,
    saved_history: RevisionHistory,
) -> None:
    saved_history.create_branch("feature")
    repository_branch_id = saved_history.manuscript_id

    branch = service.execute(
        manuscript_id=repository_branch_id,
        branch_name="feature",
    )

    assert branch.name == "feature"


def test_get_nonexistent_branch_fails(
    service: GetBranchService,
    saved_history: RevisionHistory,
) -> None:
    with pytest.raises(BranchNotFoundError):
        service.execute(
            manuscript_id=saved_history.manuscript_id,
            branch_name="missing",
        )


def test_get_branch_for_missing_history_fails(
    service: GetBranchService,
) -> None:
    with pytest.raises(ValueError, match="Revision history not found"):
        service.execute(
            manuscript_id=uuid4(),
            branch_name="feature",
        )
