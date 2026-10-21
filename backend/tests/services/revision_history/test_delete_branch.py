from uuid import uuid4

import pytest

from domain.revision_history.aggregates import RevisionHistory
from domain.revision_history.exceptions import (
    BranchNotFoundError,
    InvalidRevisionError,
)
from domain.revision_history.value_objects import CommitMessage, Snapshot
from repositories.revision_history.fake_revision_history_repository import (
    FakeRevisionHistoryRepository,
)
from services.revision_history.delete_branch import DeleteBranchService


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
) -> DeleteBranchService:
    return DeleteBranchService(repository)


@pytest.fixture
def saved_history(
    repository: FakeRevisionHistoryRepository,
    revision_history: RevisionHistory,
) -> RevisionHistory:
    repository.save(revision_history)
    return revision_history


def test_delete_branch(
    service: DeleteBranchService,
    saved_history: RevisionHistory,
) -> None:
    saved_history.create_branch("feature")

    service.execute(
        manuscript_id=saved_history.manuscript_id,
        branch_name="feature",
    )

    with pytest.raises(BranchNotFoundError):
        saved_history.get_branch("feature")


def test_delete_main_branch_fails(
    service: DeleteBranchService,
    saved_history: RevisionHistory,
) -> None:
    with pytest.raises(InvalidRevisionError):
        service.execute(
            manuscript_id=saved_history.manuscript_id,
            branch_name="main",
        )


def test_delete_nonexistent_branch_fails(
    service: DeleteBranchService,
    saved_history: RevisionHistory,
) -> None:
    with pytest.raises(BranchNotFoundError):
        service.execute(
            manuscript_id=saved_history.manuscript_id,
            branch_name="missing",
        )


def test_delete_branch_for_missing_history_fails(
    service: DeleteBranchService,
) -> None:
    with pytest.raises(ValueError, match="Revision history not found"):
        service.execute(
            manuscript_id=uuid4(),
            branch_name="feature",
        )


def test_delete_branch_persists_changes(
    service: DeleteBranchService,
    repository: FakeRevisionHistoryRepository,
    saved_history: RevisionHistory,
) -> None:
    saved_history.create_branch("feature")

    service.execute(
        manuscript_id=saved_history.manuscript_id,
        branch_name="feature",
    )

    persisted = repository.get_by_manuscript_id(saved_history.manuscript_id)

    assert persisted is not None
    assert all(branch.name != "feature" for branch in persisted.branches)
