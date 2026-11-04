from domain.revision_history.infrastructure.ports.revision_history_repository import (
    RevisionHistoryRepository,
)
from domain.revision_history.models.entities import Branch
from domain.revision_history.models.value_objects import ManuscriptId

from .errors import HistoryNotFound


class RenameDraftService:
    """Use case: rename a draft other than main."""

    def __init__(self, repository: RevisionHistoryRepository) -> None:
        self._repository = repository

    def execute(self, manuscript_id: str, name: str, new_name: str) -> Branch:
        """Rename the draft and return it.

        Raises:
            HistoryNotFound: if the manuscript has no revision history.
            RevisionError: if the draft is main, missing, or the new name is taken.
        """
        history = self._repository.get_by_manuscript_id(ManuscriptId.from_str(manuscript_id))
        if history is None:
            raise HistoryNotFound(manuscript_id)

        draft = history.rename_draft(name, new_name)
        self._repository.save(history)
        return draft
