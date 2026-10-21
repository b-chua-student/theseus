from uuid import UUID, uuid4

from .entities import Branch, Milestone, Revision
from .exceptions import (
    BranchNotFoundError,
    DuplicateBranchError,
    DuplicateMilestoneError,
    InvalidRevisionError,
    MergeConflictError,
    MilestoneNotFoundError,
    RevisionNotFoundError,
)
from .value_objects import CommitMessage, MergeConflict, Snapshot


class RevisionHistory:
    """Aggregate root for the revision history of one manuscript."""

    def __init__(
        self,
        project_id: UUID,
        manuscript_id: UUID,
    ) -> None:
        self._project_id = project_id
        self._manuscript_id = manuscript_id
        self._revisions: dict[UUID, Revision] = {}
        self._branches: dict[str, Branch] = {}
        self._milestones: dict[str, Milestone] = {}

    @property
    def project_id(self) -> UUID:
        return self._project_id

    @property
    def manuscript_id(self) -> UUID:
        return self._manuscript_id

    @property
    def has_revisions(self) -> bool:
        return bool(self._revisions)

    @property
    def revisions(self) -> tuple[Revision, ...]:
        return tuple(self._revisions.values())

    @property
    def branches(self) -> tuple[Branch, ...]:
        return tuple(
            Branch(name=branch.name, head_id=branch.head_id) for branch in self._branches.values()
        )

    @property
    def milestones(self) -> tuple[Milestone, ...]:
        return tuple(self._milestones.values())

    def initialize(
        self,
        snapshot: Snapshot,
        message: CommitMessage,
    ) -> Revision:
        """Create the initial revision when the manuscript has content."""

        if self._revisions:
            raise InvalidRevisionError("Revision history is already initialized")

        revision = Revision(
            id=uuid4(),
            parent_ids=(),
            message=message,
            snapshot=snapshot,
        )

        self._revisions[revision.id] = revision
        self._branches["main"] = Branch(
            name="main",
            head_id=revision.id,
        )

        return revision

    def get_revision(self, revision_id: UUID) -> Revision:
        try:
            return self._revisions[revision_id]
        except KeyError:
            raise RevisionNotFoundError(f"Revision not found: {revision_id}") from None

    def get_branch(self, name: str) -> Branch:
        branch = self._get_branch(name)
        return Branch(name=branch.name, head_id=branch.head_id)

    def get_branch_head(self, name: str) -> Revision:
        branch = self._get_branch(name)
        return self.get_revision(branch.head_id)

    def commit(
        self,
        branch_name: str,
        snapshot: Snapshot,
        message: CommitMessage,
    ) -> Revision:
        """Create a revision on an existing branch."""

        branch = self._get_branch(branch_name)

        revision = Revision(
            id=uuid4(),
            parent_ids=(branch.head_id,),
            message=message,
            snapshot=snapshot,
        )

        self._revisions[revision.id] = revision
        branch.advance_to(revision.id)

        return revision

    def create_branch(
        self,
        name: str,
        from_revision_id: UUID | None = None,
    ) -> Branch:
        name = name.strip()

        if not name:
            raise ValueError("Branch name cannot be empty")

        if name in self._branches:
            raise DuplicateBranchError(f"Branch already exists: {name}")

        if not self._revisions:
            raise InvalidRevisionError("Cannot create a branch before the initial revision")

        if from_revision_id is None:
            from_revision_id = self._get_branch("main").head_id
        else:
            self.get_revision(from_revision_id)

        branch = Branch(name=name, head_id=from_revision_id)
        self._branches[name] = branch

        return Branch(name=branch.name, head_id=branch.head_id)

    def delete_branch(self, name: str) -> None:
        name = name.strip()

        if not name:
            raise ValueError("Branch name cannot be empty")

        if name == "main":
            raise InvalidRevisionError("Cannot delete the main branch")

        if name not in self._branches:
            raise BranchNotFoundError(f"Branch not found: {name}")

        del self._branches[name]

    def restore(
        self,
        branch_name: str,
        target_revision_id: UUID,
        message: CommitMessage,
    ) -> Revision:
        """Restore an earlier state by creating a new revision."""

        self._get_branch(branch_name)
        target = self.get_revision(target_revision_id)

        return self.commit(
            branch_name=branch_name,
            snapshot=target.snapshot,
            message=message,
        )

    def add_milestone(
        self,
        name: str,
        revision_id: UUID,
    ) -> Milestone:
        name = name.strip()

        if not name:
            raise ValueError("Milestone name cannot be empty")

        if name in self._milestones:
            raise DuplicateMilestoneError(f"Milestone already exists: {name}")

        self.get_revision(revision_id)

        milestone = Milestone(name=name, revision_id=revision_id)
        self._milestones[name] = milestone

        return milestone

    def get_milestone(self, name: str) -> Milestone:
        try:
            return self._milestones[name]
        except KeyError:
            raise MilestoneNotFoundError(f"Milestone not found: {name}") from None

    def merge(
        self,
        source_branch_name: str,
        target_branch_name: str,
        snapshot: Snapshot,
        message: CommitMessage,
        conflicts: tuple[MergeConflict, ...] = (),
    ) -> Revision:
        if source_branch_name == target_branch_name:
            raise InvalidRevisionError("Cannot merge a branch into itself")

        source = self._get_branch(source_branch_name)
        target = self._get_branch(target_branch_name)

        if conflicts:
            raise MergeConflictError(f"Merge has {len(conflicts)} unresolved conflict(s)")

        revision = Revision(
            id=uuid4(),
            parent_ids=(target.head_id, source.head_id),
            message=message,
            snapshot=snapshot,
        )

        self._revisions[revision.id] = revision
        target.advance_to(revision.id)

        return revision

    def _get_branch(self, name: str) -> Branch:
        try:
            return self._branches[name]
        except KeyError:
            raise BranchNotFoundError(f"Branch not found: {name}") from None
