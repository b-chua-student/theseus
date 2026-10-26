from uuid import UUID

from domain.manuscript.aggregates import Manuscript
from repositories.manuscript.manuscript_repository import ManuscriptRepository


class GetAllManuscriptService:
    """Application service for retrieving all manuscripts, optionally filtered by project."""

    def __init__(self, repository: ManuscriptRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to persist manuscripts.
        """
        self._repository = repository

    def execute(self, project_id: UUID | None = None) -> list[Manuscript]:
        """Fetch manuscripts from the repository.

        Args:
            project_id: When provided, only manuscripts belonging to this
                project are returned. When None, all manuscripts are returned.

        Returns:
            A list of matching manuscripts.
        """
        if project_id is not None:
            return self._repository.get_by_project_id(project_id)
        return self._repository.get_all()
