from dataclasses import dataclass
from uuid import UUID

from domain.manuscript.aggregates import Manuscript


@dataclass(frozen=True)
class ManuscriptResponseDTO:
    id: UUID
    project_id: UUID
    title: str

    @classmethod
    def from_domain(
        cls,
        manuscript: Manuscript,
    ) -> ManuscriptResponseDTO:
        return cls(
            id=manuscript.id,
            project_id=manuscript.project_id,
            title=manuscript.title,
        )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "title": self.title,
        }
