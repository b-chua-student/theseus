from uuid import UUID, uuid4

from domain.manuscript.aggregates import Manuscript
from repositories.manuscript.manuscript_repository import ManuscriptRepository


class CreateManuscriptService:
    """Application service for creating a new manuscript within a project."""

    def __init__(self, repository: ManuscriptRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to persist manuscripts.
        """
        self._repository = repository

    def execute(
        self,
        project_id: UUID,
        title: str,
    ) -> Manuscript:
        """Create and persist a manuscript.

        Args:
            project_id: Identifier of the owning project.
            title: Title of the manuscript.

        Returns:
            The newly created manuscript.

        Raises:
            ValueError: If the title is empty or whitespace only.
        """
        manuscript = Manuscript(
            id=uuid4(),
            project_id=project_id,
            title=title,
        )

        self._repository.save(manuscript)

        return manuscript
