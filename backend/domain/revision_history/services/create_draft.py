from domain.revision_history.infrastructure.ports.revision_history_repository import (
    RevisionHistoryRepository,
)
from domain.revision_history.models.entities import Branch
from domain.revision_history.models.value_objects import ManuscriptId, RevisionId

from .errors import HistoryNotFound


class CreateDraftService:
    """Use case: create a new draft from the main draft or a past revision."""

    def __init__(self, repository: RevisionHistoryRepository) -> None:
        self._repository = repository

    def execute(self, manuscript_id: str, name: str, from_revision_id: str | None = None) -> Branch:
        """Create and persist a new draft, returning it.

        Raises:
            HistoryNotFound: if the manuscript has no revision history.
            RevisionError: if the name is taken or the source revision is unknown.
        """
        history = self._repository.get_by_manuscript_id(ManuscriptId.from_str(manuscript_id))
        if history is None:
            raise HistoryNotFound(manuscript_id)

        draft = history.create_branch(
            name,
            RevisionId.from_str(from_revision_id) if from_revision_id else None,
        )
        self._repository.save(history)
        return draft
