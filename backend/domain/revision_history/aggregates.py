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
    """Aggregate root for the revision history of a single manuscript.

    Manages revisions, branches, and milestones associated with a manuscript.
    Supports initializing revision history, committing changes, creating and
    deleting branches, restoring previous states, marking milestones, and
    merging branches.

    Attributes:
        project_id: UUID of the project containing the manuscript.
        manuscript_id: UUID of the manuscript associated with this history.
    """

    def __init__(
        self,
        project_id: UUID,
        manuscript_id: UUID,
    ) -> None:
        """Initialize the revision history for a manuscript.

        Args:
            project_id: UUID of the project containing the manuscript.
            manuscript_id: UUID of the manuscript whose history is managed.
        """
        self._project_id = project_id
        self._manuscript_id = manuscript_id
        self._revisions: dict[UUID, Revision] = {}
        self._branches: dict[str, Branch] = {}
        self._milestones: dict[str, Milestone] = {}

    @property
    def project_id(self) -> UUID:
        """Return the UUID of the project containing the manuscript.

        Returns:
            The project's UUID.
        """
        return self._project_id

    @property
    def manuscript_id(self) -> UUID:
        """Return the UUID of the manuscript associated with this history.

        Returns:
            The manuscript's UUID.
        """
        return self._manuscript_id

    @property
    def has_revisions(self) -> bool:
        """Indicate whether the revision history contains any revisions.

        Returns:
            True if at least one revision exists; otherwise, False.
        """
        return bool(self._revisions)

    @property
    def revisions(self) -> tuple[Revision, ...]:
        """Return all revisions in the history.

        Returns:
            An immutable tuple containing the revisions in insertion order.
        """
        return tuple(self._revisions.values())

    @property
    def branches(self) -> tuple[Branch, ...]:
        """Return copies of all branches in the revision history.

        Returns:
            An immutable tuple containing copies of the branches.
        """
        return tuple(
            Branch(name=branch.name, head_id=branch.head_id) for branch in self._branches.values()
        )

    @property
    def milestones(self) -> tuple[Milestone, ...]:
        """Return all milestones in the revision history.

        Returns:
            An immutable tuple containing the milestones in insertion order.
        """
        return tuple(self._milestones.values())

    def initialize(
        self,
        snapshot: Snapshot,
        message: CommitMessage,
    ) -> Revision:
        """Initialize the history with its first revision.

        Creates the initial revision and a ``main`` branch pointing to it.
        This operation is only permitted when the history contains no
        existing revisions.

        Args:
            snapshot: Snapshot representing the manuscript's initial state.
            message: Commit message describing the initial revision.

        Returns:
            The newly created initial revision.

        Raises:
            InvalidRevisionError: If the revision history is already
                initialized.
        """
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
        """Retrieve a revision by its UUID.

        Args:
            revision_id: UUID of the revision to retrieve.

        Returns:
            The requested revision.

        Raises:
            RevisionNotFoundError: If no revision exists with the given UUID.
        """
        try:
            return self._revisions[revision_id]
        except KeyError:
            raise RevisionNotFoundError(f"Revision not found: {revision_id}") from None

    def get_branch(self, name: str) -> Branch:
        """Retrieve a copy of a branch by name.

        Args:
            name: Name of the branch to retrieve.

        Returns:
            A copy of the requested branch.

        Raises:
            BranchNotFoundError: If the branch does not exist.
        """
        branch = self._get_branch(name)
        return Branch(name=branch.name, head_id=branch.head_id)

    def get_branch_head(self, name: str) -> Revision:
        """Retrieve the latest revision referenced by a branch.

        Args:
            name: Name of the branch whose head revision is requested.

        Returns:
            The revision currently referenced by the branch.

        Raises:
            BranchNotFoundError: If the branch does not exist.
            RevisionNotFoundError: If the branch references a nonexistent
                revision.
        """
        branch = self._get_branch(name)
        return self.get_revision(branch.head_id)

    def commit(
        self,
        branch_name: str,
        snapshot: Snapshot,
        message: CommitMessage,
    ) -> Revision:
        """Create a new revision on an existing branch.

        The new revision uses the branch's current head as its parent and
        advances the branch to the newly created revision.

        Args:
            branch_name: Name of the branch receiving the new revision.
            snapshot: Snapshot representing the manuscript's new state.
            message: Commit message describing the changes.

        Returns:
            The newly created revision.

        Raises:
            BranchNotFoundError: If the specified branch does not exist.
        """
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
        """Create a new branch from an existing revision.

        If no starting revision is specified, the new branch starts at the
        current head of ``main``.

        Args:
            name: Name of the branch to create. Leading and trailing
                whitespace is removed.
            from_revision_id: UUID of the revision from which the branch
                starts. Defaults to the current head of ``main``.

        Returns:
            A copy of the newly created branch.

        Raises:
            ValueError: If the branch name is empty after trimming whitespace.
            DuplicateBranchError: If a branch with the specified name
                already exists.
            InvalidRevisionError: If the history has not been initialized.
            BranchNotFoundError: If ``main`` does not exist when no starting
                revision is specified.
            RevisionNotFoundError: If ``from_revision_id`` does not identify
                an existing revision.
        """
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
        """Delete an existing branch.

        The ``main`` branch cannot be deleted.

        Args:
            name: Name of the branch to delete. Leading and trailing
                whitespace is removed.

        Raises:
            ValueError: If the branch name is empty after trimming whitespace.
            InvalidRevisionError: If an attempt is made to delete ``main``.
            BranchNotFoundError: If the specified branch does not exist.
        """
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
        """Restore a previous manuscript state on a branch.

        Creates a new revision using the snapshot from the target revision.
        The target revision remains unchanged, and the new revision's parent
        is the branch's current head.

        Args:
            branch_name: Name of the branch on which to create the revision.
            target_revision_id: UUID of the revision whose snapshot should
                be restored.
            message: Commit message describing the restoration.

        Returns:
            The newly created revision containing the restored snapshot.

        Raises:
            BranchNotFoundError: If the specified branch does not exist.
            RevisionNotFoundError: If the target revision does not exist.
        """
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
        """Create a named milestone pointing to an existing revision.

        Args:
            name: Name of the milestone. Leading and trailing whitespace
                is removed.
            revision_id: UUID of the revision to associate with the milestone.

        Returns:
            The newly created milestone.

        Raises:
            ValueError: If the milestone name is empty after trimming
                whitespace.
            DuplicateMilestoneError: If a milestone with the specified name
                already exists.
            RevisionNotFoundError: If the specified revision does not exist.
        """
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
        """Retrieve a milestone by name.

        Args:
            name: Name of the milestone to retrieve.

        Returns:
            The requested milestone.

        Raises:
            MilestoneNotFoundError: If no milestone exists with the given name.
        """
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
        """Merge one branch into another by creating a new revision.

        The new revision has both the target branch's current head and the
        source branch's current head as parents. On success, the target
        branch advances to the new revision, while the source branch remains
        unchanged.

        The caller is responsible for producing the merged snapshot and
        identifying any unresolved conflicts before invoking this method.

        Args:
            source_branch_name: Name of the branch whose changes are merged.
            target_branch_name: Name of the branch receiving the merge.
            snapshot: Snapshot representing the merged manuscript state.
            message: Commit message describing the merge.
            conflicts: Unresolved conflicts detected during the merge.
                Defaults to an empty tuple.

        Returns:
            The newly created merge revision.

        Raises:
            InvalidRevisionError: If the source and target branch names
                are identical.
            BranchNotFoundError: If either branch does not exist.
            MergeConflictError: If unresolved conflicts are provided.
        """
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
        """Retrieve an internal branch by name.

        Unlike ``get_branch``, this method returns the stored branch instance
        so internal operations can update its head.

        Args:
            name: Name of the branch to retrieve.

        Returns:
            The stored branch instance.

        Raises:
            BranchNotFoundError: If the branch does not exist.
        """
        try:
            return self._branches[name]
        except KeyError:
            raise BranchNotFoundError(f"Branch not found: {name}") from None
