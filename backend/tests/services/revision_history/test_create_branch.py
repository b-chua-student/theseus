from uuid import uuid4

import pytest

from repositories.revision_history.fake_revision_history_repository import (
    FakeRevisionHistoryRepository,
)
from services.revision_history.create_branch import CreateBranchService
from domain.revision_history.aggregates import RevisionHistory
from domain.revision_history.exceptions import (
    BranchNotFoundError,
    DuplicateBranchError,
    RevisionNotFoundError,
)
from domain.revision_history.value_objects import CommitMessage, Snapshot


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
) -> CreateBranchService:
    return CreateBranchService(repository)


@pytest.fixture
def saved_history(
    repository: FakeRevisionHistoryRepository,
    revision_history: RevisionHistory,
) -> RevisionHistory:
    repository.save(revision_history)
    return revision_history


def test_create_branch(
    service: CreateBranchService,
    saved_history: RevisionHistory,
) -> None:
    branch = service.execute(
        manuscript_id=saved_history.manuscript_id,
        branch_name="feature",
    )

    assert branch.name == "feature"
    assert branch.head_id == saved_history.get_branch("main").head_id


def test_create_branch_from_specific_revision(
    service: CreateBranchService,
    saved_history: RevisionHistory,
) -> None:
    revision = saved_history.revisions[0]

    branch = service.execute(
        manuscript_id=saved_history.manuscript_id,
        branch_name="feature",
        revision_id=revision.id,
    )

    assert branch.head_id == revision.id


def test_create_branch_with_empty_name_fails(
    service: CreateBranchService,
    saved_history: RevisionHistory,
) -> None:
    with pytest.raises(ValueError, match="Branch name cannot be empty"):
        service.execute(
            manuscript_id=saved_history.manuscript_id,
            branch_name="   ",
        )


def test_create_duplicate_branch_fails(
    service: CreateBranchService,
    saved_history: RevisionHistory,
) -> None:
    service.execute(
        manuscript_id=saved_history.manuscript_id,
        branch_name="feature",
    )

    with pytest.raises(DuplicateBranchError):
        service.execute(
            manuscript_id=saved_history.manuscript_id,
            branch_name="feature",
        )


def test_create_branch_from_nonexistent_revision_fails(
    service: CreateBranchService,
    saved_history: RevisionHistory,
) -> None:
    with pytest.raises(RevisionNotFoundError):
        service.execute(
            manuscript_id=saved_history.manuscript_id,
            branch_name="feature",
            revision_id=uuid4(),
        )


def test_create_branch_for_missing_history_fails(
    service: CreateBranchService,
) -> None:
    with pytest.raises(ValueError, match="Revision history not found"):
        service.execute(
            manuscript_id=uuid4(),
            branch_name="feature",
        )


def test_create_branch_persists_history(
    service: CreateBranchService,
    repository: FakeRevisionHistoryRepository,
    saved_history: RevisionHistory,
) -> None:
    service.execute(
        manuscript_id=saved_history.manuscript_id,
        branch_name="feature",
    )

    persisted = repository.get_by_manuscript_id(
        saved_history.manuscript_id
    )

    assert persisted is not None
    assert any(branch.name == "feature" for branch in persisted.branches)
