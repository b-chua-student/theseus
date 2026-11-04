from dataclasses import dataclass

from domain.manuscript.infrastructure.ports.manuscript_repository import ManuscriptRepository
from domain.manuscript.models.value_objects import ProjectId


@dataclass
class ManuscriptInfoDTO:
    """Summary of a manuscript (ids and title as plain strings) for listings."""

    id: str
    project_id: str
    title: str


class ListManuscriptsService:
    """Use case: list the manuscripts of a project."""

    def __init__(self, repository: ManuscriptRepository) -> None:
        self._repository = repository

    def execute(self, project_id: str) -> list[ManuscriptInfoDTO]:
        """Return summaries of all manuscripts in the project."""
        manuscript_info_dtos = []

        valid_project_id = ProjectId.from_str(project_id)

        manuscripts = self._repository.list_by_project_id(valid_project_id)

        for manuscript in manuscripts:
            manuscript_info_dtos.append(
                ManuscriptInfoDTO(
                    id=str(manuscript.id.value),
                    project_id=str(manuscript.project_id.value),
                    title=str(manuscript.title.value),
                )
            )

        return manuscript_info_dtos
