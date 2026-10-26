from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from domain.project.aggregates import Project


@dataclass(frozen=True)
class ProjectResponseDTO:
    """Immutable response DTO representing a project.

    Attributes:
        id: Unique identifier of the project.
        owner_id: ID of the owning user.
        name: Name of the project.
    """

    id: UUID
    owner_id: UUID
    name: str

    @classmethod
    def from_domain(cls, project: Project) -> ProjectResponseDTO:
        """Build a DTO from a domain project.

        Args:
            project: Project aggregate to convert.

        Returns:
            DTO populated from the project.
        """
        return cls(
            id=project.id,
            owner_id=project.owner_id,
            name=project.name.value,
        )

    def to_dict(self) -> dict:
        """Serialize the DTO to a JSON-compatible dictionary.

        Returns:
            Dictionary with UUIDs converted to strings.
        """
        return {
            "id": str(self.id),
            "owner_id": str(self.owner_id),
            "name": self.name,
        }
