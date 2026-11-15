from domain.src_lib.infrastructure.ports.source_repository import SourceRepository
from domain.src_lib.models.aggregates import Source


class ListSourcesService:
    """Use case: list all sources that have not been removed."""

    def __init__(self, repository: SourceRepository) -> None:
        self._repository = repository

    def execute(self) -> list[Source]:
        """Return all active sources."""
        return self._repository.list_active()
