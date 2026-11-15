from domain.manuscript.infrastructure.ports.manuscript_repository import ManuscriptRepository
from domain.manuscript.models.aggregates import Manuscript
from domain.manuscript.models.value_objects import ManuscriptId


class GetManuscriptService:
    """Use case: fetch a manuscript by id."""

    def __init__(self, repository: ManuscriptRepository) -> None:
        self._repository = repository

    def execute(self, manuscript_id: str) -> Manuscript | None:
        """Return the manuscript, or None if it does not exist."""
        valid_manuscript_id = ManuscriptId.from_str(manuscript_id)

        return self._repository.get_by_id(valid_manuscript_id)
