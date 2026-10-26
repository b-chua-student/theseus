from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from domain.revision_history.aggregates import RevisionHistory
from domain.revision_history.entities import Branch, Milestone, Revision


@dataclass(frozen=True)
class RevisionResponseDTO:
    """Immutable response DTO for a single revision.

    Attributes:
        id: UUID of the revision.
        parent_ids: Tuple of parent revision UUIDs.
        message: Commit message value.
        tree_hash: Snapshot tree hash.
    """

    id: UUID
    parent_ids: tuple[UUID, ...]
    message: str
    tree_hash: str

    @classmethod
    def from_domain(cls, revision: Revision) -> RevisionResponseDTO:
        """Build a DTO from a domain Revision.

        Args:
            revision: Revision entity to convert.

        Returns:
            DTO populated from the revision.
        """
        return cls(
            id=revision.id,
            parent_ids=revision.parent_ids,
            message=revision.message.value,
            tree_hash=revision.snapshot.tree_hash,
        )

    def to_dict(self) -> dict:
        """Serialize the DTO to a JSON-compatible dictionary.

        Returns:
            Dictionary with UUIDs converted to strings.
        """
        return {
            "id": str(self.id),
            "parent_ids": [str(pid) for pid in self.parent_ids],
            "message": self.message,
            "tree_hash": self.tree_hash,
        }


@dataclass(frozen=True)
class BranchResponseDTO:
    """Immutable response DTO for a branch.

    Attributes:
        name: Branch name.
        head_id: UUID of the revision the branch currently points to.
    """

    name: str
    head_id: UUID

    @classmethod
    def from_domain(cls, branch: Branch) -> BranchResponseDTO:
        """Build a DTO from a domain Branch.

        Args:
            branch: Branch entity to convert.

        Returns:
            DTO populated from the branch.
        """
        return cls(name=branch.name, head_id=branch.head_id)

    def to_dict(self) -> dict:
        """Serialize the DTO to a JSON-compatible dictionary.

        Returns:
            Dictionary with UUID converted to string.
        """
        return {
            "name": self.name,
            "head_id": str(self.head_id),
        }


@dataclass(frozen=True)
class MilestoneResponseDTO:
    """Immutable response DTO for a milestone.

    Attributes:
        name: Milestone name.
        revision_id: UUID of the revision the milestone points to.
    """

    name: str
    revision_id: UUID

    @classmethod
    def from_domain(cls, milestone: Milestone) -> MilestoneResponseDTO:
        """Build a DTO from a domain Milestone.

        Args:
            milestone: Milestone entity to convert.

        Returns:
            DTO populated from the milestone.
        """
        return cls(name=milestone.name, revision_id=milestone.revision_id)

    def to_dict(self) -> dict:
        """Serialize the DTO to a JSON-compatible dictionary.

        Returns:
            Dictionary with UUID converted to string.
        """
        return {
            "name": self.name,
            "revision_id": str(self.revision_id),
        }


@dataclass(frozen=True)
class RevisionHistoryResponseDTO:
    """Immutable response DTO for a revision history aggregate.

    Attributes:
        project_id: UUID of the owning project.
        manuscript_id: UUID of the manuscript.
        has_revisions: Whether the history contains any revisions.
        revisions: All revisions in insertion order.
        branches: All branches.
        milestones: All milestones.
    """

    project_id: UUID
    manuscript_id: UUID
    has_revisions: bool
    revisions: tuple[RevisionResponseDTO, ...]
    branches: tuple[BranchResponseDTO, ...]
    milestones: tuple[MilestoneResponseDTO, ...]

    @classmethod
    def from_domain(cls, history: RevisionHistory) -> RevisionHistoryResponseDTO:
        """Build a DTO from a RevisionHistory aggregate.

        Args:
            history: Revision history aggregate to convert.

        Returns:
            DTO populated from the history.
        """
        return cls(
            project_id=history.project_id,
            manuscript_id=history.manuscript_id,
            has_revisions=history.has_revisions,
            revisions=tuple(RevisionResponseDTO.from_domain(r) for r in history.revisions),
            branches=tuple(BranchResponseDTO.from_domain(b) for b in history.branches),
            milestones=tuple(MilestoneResponseDTO.from_domain(m) for m in history.milestones),
        )

    def to_dict(self) -> dict:
        """Serialize the DTO to a JSON-compatible dictionary.

        Returns:
            Nested dictionary with all UUIDs converted to strings.
        """
        return {
            "project_id": str(self.project_id),
            "manuscript_id": str(self.manuscript_id),
            "has_revisions": self.has_revisions,
            "revisions": [r.to_dict() for r in self.revisions],
            "branches": [b.to_dict() for b in self.branches],
            "milestones": [m.to_dict() for m in self.milestones],
        }
