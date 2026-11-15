from domain.revision_history.infrastructure.ports.revision_history_repository import (
    RevisionHistoryRepository,
)
from domain.revision_history.models.entities import Revision
from domain.revision_history.models.value_objects import ManuscriptId, RevisionId

from .errors import HistoryNotFound


class GetRevisionService:
    """Use case: fetch a single revision by ID."""

    def __init__(self, repository: RevisionHistoryRepository) -> None:
        self._repository = repository

    def execute(self, manuscript_id: str, revision_id: str) -> Revision:
        """Return the revision with the given ID.

        Raises:
            HistoryNotFound: if the manuscript has no revision history.
            RevisionError: if the revision does not exist.
        """
        history = self._repository.get_by_manuscript_id(ManuscriptId.from_str(manuscript_id))
        if history is None:
            raise HistoryNotFound(manuscript_id)

        return history.get_revision(RevisionId.from_str(revision_id))
