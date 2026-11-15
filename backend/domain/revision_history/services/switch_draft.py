from domain.revision_history.infrastructure.ports.manuscript_writer import ManuscriptWriter
from domain.revision_history.infrastructure.ports.revision_history_repository import (
    RevisionHistoryRepository,
)
from domain.revision_history.models.entities import Branch
from domain.revision_history.models.value_objects import ManuscriptId

from .errors import HistoryNotFound


class SwitchDraftService:
    """Make a draft current; the manuscript content becomes that draft's latest revision."""

    def __init__(self, repository: RevisionHistoryRepository, writer: ManuscriptWriter) -> None:
        self._repository = repository
        self._writer = writer

    def execute(self, manuscript_id: str, name: str) -> Branch:
        """Switch to the named draft, apply its head snapshot, and return it.

        Raises:
            HistoryNotFound: if the manuscript has no revision history.
            RevisionError: if the draft does not exist.
        """
        valid_id = ManuscriptId.from_str(manuscript_id)
        history = self._repository.get_by_manuscript_id(valid_id)
        if history is None:
            raise HistoryNotFound(manuscript_id)

        draft = history.switch_draft(name)
        self._writer.apply_snapshot(str(valid_id.value), draft.head.snapshot)
        self._repository.save(history)
        return draft
