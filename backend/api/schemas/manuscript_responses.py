from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from domain.manuscript.aggregates import Manuscript


@dataclass(frozen=True)
class ManuscriptResponseDTO:
    """Immutable response DTO representing a manuscript.

    Attributes:
        id: Unique identifier of the manuscript.
        project_id: ID of the project the manuscript belongs to.
        title: Title of the manuscript.
    """

    id: UUID
    project_id: UUID
    title: str

    @classmethod
    def from_domain(
        cls,
        manuscript: Manuscript,
    ) -> ManuscriptResponseDTO:
        """Build a DTO from a domain manuscript.

        Args:
            manuscript: Manuscript aggregate to convert.

        Returns:
            DTO populated from the manuscript.
        """
        return cls(
            id=manuscript.id,
            project_id=manuscript.project_id,
            title=manuscript.title,
        )

    def to_dict(self) -> dict:
        """Serialize the DTO to a JSON-compatible dictionary.

        Returns:
            Dictionary with UUIDs converted to strings.
        """
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "title": self.title,
        }
