from domain.revision_history.infrastructure.ports.revision_history_repository import (
    RevisionHistoryRepository,
)
from domain.revision_history.models.entities import Branch
from domain.revision_history.models.value_objects import ManuscriptId

from .errors import HistoryNotFound


class ListDraftsService:
    """Use case: list all drafts of a manuscript."""

    def __init__(self, repository: RevisionHistoryRepository) -> None:
        self._repository = repository

    def execute(self, manuscript_id: str) -> tuple[list[Branch], str]:
        """Return all drafts and the name of the current draft."""
        history = self._repository.get_by_manuscript_id(ManuscriptId.from_str(manuscript_id))
        if history is None:
            raise HistoryNotFound(manuscript_id)

        return list(history.branches), history.current_draft.name
