from domain.revision_history.aggregates import RevisionHistory
from repositories.revision_history.revision_history_repository import RevisionHistoryRepository


class GetAllHistoriesService:
    """Application service for retrieving all revision histories."""

    def __init__(self, repository: RevisionHistoryRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to fetch revision histories.
        """
        self._repository = repository

    def execute(self) -> list[RevisionHistory]:
        """Retrieve all revision histories.

        Returns:
            A list of all stored revision histories.
        """
        return self._repository.get_all()
