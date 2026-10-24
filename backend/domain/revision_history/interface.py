from abc import ABC, abstractmethod
from uuid import UUID

from .entities import Branch, Milestone, Revision
from .value_objects import CommitMessage, MergeConflict, Snapshot


class AbstractRevisionHistory(ABC):
    """Contract for the revision history of a single manuscript.

    Manages revisions, branches, and milestones. Supports initializing,
    committing, branching, restoring, marking milestones, and merging.
    """

    @property
    @abstractmethod
    def project_id(self) -> UUID:
        """UUID of the project containing the manuscript."""

    @property
    @abstractmethod
    def manuscript_id(self) -> UUID:
        """UUID of the manuscript associated with this history."""

    @property
    @abstractmethod
    def has_revisions(self) -> bool:
        """True if at least one revision exists."""

    @property
    @abstractmethod
    def revisions(self) -> tuple[Revision, ...]:
        """All revisions, in insertion order."""

    @property
    @abstractmethod
    def branches(self) -> tuple[Branch, ...]:
        """Copies of all branches."""

    @property
    @abstractmethod
    def milestones(self) -> tuple[Milestone, ...]:
        """All milestones, in insertion order."""

    @abstractmethod
    def initialize(self, snapshot: Snapshot, message: CommitMessage) -> Revision:
        """Create the first revision and a ``main`` branch pointing to it.

        Raises:
            InvalidRevisionError: If the history is already initialized.
        """

    @abstractmethod
    def get_revision(self, revision_id: UUID) -> Revision:
        """Return a revision by id.

        Raises:
            RevisionNotFoundError: If it does not exist.
        """

    @abstractmethod
    def get_branch(self, name: str) -> Branch:
        """Return a copy of a branch by name.

        Raises:
            BranchNotFoundError: If it does not exist.
        """

    @abstractmethod
    def get_branch_head(self, name: str) -> Revision:
        """Return the revision a branch currently points to.

        Raises:
            BranchNotFoundError: If the branch does not exist.
            RevisionNotFoundError: If the head revision does not exist.
        """

    @abstractmethod
    def commit(
        self,
        branch_name: str,
        snapshot: Snapshot,
        message: CommitMessage,
    ) -> Revision:
        """Create a revision on a branch and advance the branch to it.

        Raises:
            BranchNotFoundError: If the branch does not exist.
        """

    @abstractmethod
    def create_branch(
        self,
        name: str,
        from_revision_id: UUID | None = None,
    ) -> Branch:
        """Create a branch. Starts at the head of ``main`` by default.

        Raises:
            ValueError: If the name is empty after stripping.
            DuplicateBranchError: If the name is taken.
            InvalidRevisionError: If the history is not initialized.
            BranchNotFoundError: If ``main`` is missing and no revision is given.
            RevisionNotFoundError: If ``from_revision_id`` does not exist.
        """

    @abstractmethod
    def delete_branch(self, name: str) -> None:
        """Delete a branch. ``main`` cannot be deleted.

        Raises:
            ValueError: If the name is empty after stripping.
            InvalidRevisionError: If the branch is ``main``.
            BranchNotFoundError: If the branch does not exist.
        """

    @abstractmethod
    def restore(
        self,
        branch_name: str,
        target_revision_id: UUID,
        message: CommitMessage,
    ) -> Revision:
        """Commit the target revision's snapshot as a new revision on a branch.

        Raises:
            BranchNotFoundError: If the branch does not exist.
            RevisionNotFoundError: If the target revision does not exist.
        """

    @abstractmethod
    def add_milestone(self, name: str, revision_id: UUID) -> Milestone:
        """Create a named milestone pointing to a revision.

        Raises:
            ValueError: If the name is empty after stripping.
            DuplicateMilestoneError: If the name is taken.
            RevisionNotFoundError: If the revision does not exist.
        """

    @abstractmethod
    def get_milestone(self, name: str) -> Milestone:
        """Return a milestone by name.

        Raises:
            MilestoneNotFoundError: If it does not exist.
        """

    @abstractmethod
    def merge(
        self,
        source_branch_name: str,
        target_branch_name: str,
        snapshot: Snapshot,
        message: CommitMessage,
        conflicts: tuple[MergeConflict, ...] = (),
    ) -> Revision:
        """Merge source into target via a new two-parent revision.

        The caller supplies the merged snapshot and any unresolved conflicts.

        Raises:
            InvalidRevisionError: If source and target are the same.
            BranchNotFoundError: If either branch does not exist.
            MergeConflictError: If unresolved conflicts are provided.
        """
