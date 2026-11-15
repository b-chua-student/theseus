from domain.manuscript.infrastructure.ports.manuscript_repository import ManuscriptRepository
from domain.manuscript.models.value_objects import ManuscriptId


class DeleteManuscriptService:
    """Use case: delete a manuscript."""

    def __init__(self, repository: ManuscriptRepository) -> None:
        self._repository = repository

    def execute(self, manuscript_id: str) -> None:
        """Delete the manuscript with the given id."""
        valid_manuscript_id = ManuscriptId.from_str(manuscript_id)

        self._repository.delete(valid_manuscript_id)
