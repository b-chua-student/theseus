from dataclasses import dataclass, field
from datetime import datetime

from domain.shared.clock import now

from .value_objects import RevisionId, Snapshot


@dataclass(frozen=True)
class Revision:
    """Immutable point-in-time capture of a manuscript with a commit message."""

    id: RevisionId
    message: str
    snapshot: Snapshot
    created_at: datetime = field(default_factory=now)


@dataclass(eq=False)
class Branch:
    """Named draft holding an ordered list of revisions, oldest first."""

    name: str
    revisions: list[Revision] = field(default_factory=list)

    @property
    def head(self) -> Revision:
        """The latest revision on this branch."""
        return self.revisions[-1]

    def append(self, revision: Revision) -> None:
        """Add a revision as the new head of this branch."""
        self.revisions.append(revision)
