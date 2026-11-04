from __future__ import annotations

from .entities import Branch, Revision
from .errors import NoChangesError, RevisionError
from .value_objects import (
    ManuscriptId,
    RevisionId,
    Snapshot,
)

MAIN = "main"


class RevisionHistory:
    """Aggregate root tracking a manuscript's revisions across named drafts (branches).

    Invariant: a ``main`` branch always exists once the history is started, and
    exactly one branch is current at any time.
    """

    def __init__(self, manuscript_id: ManuscriptId) -> None:
        self.manuscript_id = manuscript_id
        self._branches: dict[str, Branch] = {}
        self._current: str = MAIN

    @classmethod
    def rehydrate(
        cls, manuscript_id: ManuscriptId, branches: dict[str, Branch], current: str
    ) -> RevisionHistory:
        """Rebuild a history from persisted state (used by repositories)."""
        history = cls(manuscript_id)
        history._branches = dict(branches)
        history._current = current
        return history

    @classmethod
    def start(cls, manuscript_id: ManuscriptId, snapshot: Snapshot) -> RevisionHistory:
        """Begin tracking revision history for a manuscript with an initial revision."""
        history = cls(manuscript_id)
        first = Revision(RevisionId.new(), "Initial revision", snapshot)
        history._branches[MAIN] = Branch(MAIN, [first])
        return history

    def commit(self, branch_name: str, snapshot: Snapshot, message: str) -> Revision:
        """Append a new revision to a branch, unless the snapshot is unchanged.

        Raises:
            NoChangesError: if the snapshot matches the branch's current head.
        """
        branch = self._branch(branch_name)
        if branch.head.snapshot == snapshot:
            raise NoChangesError("No changes since the last revision.")
        revision = Revision(RevisionId.new(), message, snapshot)
        branch.append(revision)
        return revision

    def create_branch(self, name: str, from_revision_id: RevisionId | None = None) -> Branch:
        """Create a new draft copying main's revisions up to an optional point.

        Raises:
            RevisionError: if a branch with this name already exists.
        """
        if name in self._branches:
            raise RevisionError(f"Branch '{name}' already exists.")
        source = self._branches[MAIN]
        if from_revision_id is None:
            upto = list(source.revisions)
        else:
            upto = self._history_up_to(from_revision_id)
        branch = Branch(name, upto)
        self._branches[name] = branch
        return branch

    def restore(self, branch_name: str, revision_id: RevisionId) -> Revision:
        """Commit a new revision on a branch that reverts to a past revision's snapshot."""
        branch = self._branch(branch_name)
        target = next((r for r in branch.revisions if r.id == revision_id), None)
        if target is None:
            raise RevisionError("Revision not found on this branch.")
        return self.commit(branch_name, target.snapshot, f"Restore {target.id.value}")

    @property
    def current_draft(self) -> Branch:
        """The branch currently active for this manuscript."""
        return self._branch(self._current)

    def switch_draft(self, name: str) -> Branch:
        """Make the named branch the current draft."""
        branch = self._branch(name)
        self._current = name
        return branch

    def rename_draft(self, name: str, new_name: str) -> Branch:
        """Rename a non-main branch, keeping it current if it was.

        Raises:
            RevisionError: if renaming main, or if `new_name` is already taken.
        """
        if name == MAIN:
            raise RevisionError("The main draft cannot be renamed.")
        branch = self._branch(name)
        if new_name == name:
            return branch
        if new_name in self._branches:
            raise RevisionError(f"Draft '{new_name}' already exists.")
        del self._branches[name]
        branch.name = new_name
        self._branches[new_name] = branch
        if self._current == name:
            self._current = new_name
        return branch

    def delete_draft(self, name: str) -> None:
        """Delete a non-main, non-current branch.

        Raises:
            RevisionError: if deleting main or the currently active draft.
        """
        if name == MAIN:
            raise RevisionError("The main draft cannot be deleted.")
        if name == self._current:
            raise RevisionError(
                "The current draft cannot be deleted. Switch to another draft first."
            )
        self._branch(name)
        del self._branches[name]

    def get_branch(self, name: str) -> Branch:
        """Return the named branch.

        Raises:
            RevisionError: if no branch with this name exists.
        """
        return self._branch(name)

    def get_revision(self, revision_id: RevisionId) -> Revision:
        """Find a revision by ID across all branches.

        Raises:
            RevisionError: if no revision with this ID exists.
        """
        for branch in self._branches.values():
            for r in branch.revisions:
                if r.id == revision_id:
                    return r
        raise RevisionError("Revision not found.")

    @property
    def branches(self) -> tuple[Branch, ...]:
        """All branches (drafts) in this history."""
        return tuple(self._branches.values())

    def _branch(self, name: str) -> Branch:
        try:
            return self._branches[name]
        except KeyError:
            raise RevisionError(f"Branch '{name}' not found.") from None

    def _history_up_to(self, revision_id: RevisionId) -> list[Revision]:
        for branch in self._branches.values():
            for i, r in enumerate(branch.revisions):
                if r.id == revision_id:
                    return branch.revisions[: i + 1]
        raise RevisionError("Revision not found.")
