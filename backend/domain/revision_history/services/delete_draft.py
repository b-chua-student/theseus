from domain.revision_history.infrastructure.ports.revision_history_repository import (
    RevisionHistoryRepository,
)
from domain.revision_history.models.value_objects import ManuscriptId

from .errors import HistoryNotFound


class DeleteDraftService:
    """Use case: delete a draft that is neither main nor current."""

    def __init__(self, repository: RevisionHistoryRepository) -> None:
        self._repository = repository

    def execute(self, manuscript_id: str, name: str) -> None:
        """Delete the named draft.

        Raises:
            HistoryNotFound: if the manuscript has no revision history.
            RevisionError: if the draft is main, current, or does not exist.
        """
        history = self._repository.get_by_manuscript_id(ManuscriptId.from_str(manuscript_id))
        if history is None:
            raise HistoryNotFound(manuscript_id)

        history.delete_draft(name)
        self._repository.save(history)
