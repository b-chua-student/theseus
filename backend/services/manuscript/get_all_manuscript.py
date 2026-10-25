from domain.manuscript.aggregates import Manuscript
from repositories.manuscript.manuscript_repository import ManuscriptRepository


class GetAllManuscriptService:
    """Application service for retrieving all manuscripts within a project."""

    def __init__(self, repository: ManuscriptRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to persist manuscripts.
        """
        self._repository = repository

    def execute(self) -> list[Manuscript]:
        """Fetch all manuscripts from the repository."""
        return self._repository.get_all()
