from domain.revision_history.infrastructure.ports.revision_history_repository import (
    RevisionHistoryRepository,
)
from domain.revision_history.models.entities import Branch
from domain.revision_history.models.value_objects import ManuscriptId

from .errors import HistoryNotFound


class GetDraftService:
    """Use case: fetch a single draft by name."""

    def __init__(self, repository: RevisionHistoryRepository) -> None:
        self._repository = repository

    def execute(self, manuscript_id: str, name: str) -> tuple[Branch, bool]:
        """Return the draft and whether it is the current draft."""
        history = self._repository.get_by_manuscript_id(ManuscriptId.from_str(manuscript_id))
        if history is None:
            raise HistoryNotFound(manuscript_id)

        draft = history.get_branch(name)
        return draft, history.current_draft.name == draft.name
