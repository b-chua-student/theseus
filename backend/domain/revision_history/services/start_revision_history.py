from domain.revision_history.infrastructure.ports.manuscript_reader import ManuscriptReader
from domain.revision_history.infrastructure.ports.revision_history_repository import (
    RevisionHistoryRepository,
)
from domain.revision_history.models.aggregates import RevisionHistory
from domain.revision_history.models.value_objects import ManuscriptId

from .errors import ManuscriptNotFound


class StartRevisionHistoryService:
    """Use case: begin tracking revisions for a manuscript."""

    def __init__(self, repository: RevisionHistoryRepository, reader: ManuscriptReader) -> None:
        self._repository = repository
        self._reader = reader

    def execute(self, manuscript_id: str) -> None:
        """Create the history with an initial revision; do nothing if one already exists.

        Raises:
            ManuscriptNotFound: if the manuscript does not exist.
        """
        valid_id = ManuscriptId.from_str(manuscript_id)

        if self._repository.get_by_manuscript_id(valid_id) is not None:
            return

        snapshot = self._reader.get_snapshot(str(valid_id.value))
        if snapshot is None:
            raise ManuscriptNotFound(manuscript_id)

        self._repository.add(RevisionHistory.start(valid_id, snapshot))
