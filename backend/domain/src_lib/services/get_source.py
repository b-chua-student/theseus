from domain.src_lib.infrastructure.ports.source_repository import SourceRepository
from domain.src_lib.models.aggregates import Source
from domain.src_lib.models.value_objects import SourceId


class GetSourceService:
    """Use case: look up a source by ID."""

    def __init__(self, repository: SourceRepository) -> None:
        self._repository = repository

    def execute(self, source_id: str) -> Source | None:
        """Return the source, or None if it does not exist."""
        return self._repository.get(SourceId.from_str(source_id))
