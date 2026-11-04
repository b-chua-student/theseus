from domain.revision_history.infrastructure.ports.manuscript_reader import ManuscriptReader
from domain.revision_history.infrastructure.ports.revision_history_repository import (
    RevisionHistoryRepository,
)
from domain.revision_history.models.entities import Revision
from domain.revision_history.models.errors import RevisionError
from domain.revision_history.models.value_objects import ManuscriptId

from .errors import HistoryNotFound, ManuscriptNotFound


class CommitRevisionService:
    """Use case: record the manuscript's current content as a new revision."""

    def __init__(self, repository: RevisionHistoryRepository, reader: ManuscriptReader) -> None:
        self._repository = repository
        self._reader = reader

    def execute(self, manuscript_id: str, branch_name: str | None, message: str) -> Revision:
        """Commit the current manuscript content to the current draft and return the new revision.

        Raises:
            HistoryNotFound: if the manuscript has no revision history.
            ManuscriptNotFound: if the manuscript does not exist.
            RevisionError: if `branch_name` is not the current draft.
            NoChangesError: if nothing changed since the last revision.
        """
        valid_id = ManuscriptId.from_str(manuscript_id)

        history = self._repository.get_by_manuscript_id(valid_id)
        if history is None:
            raise HistoryNotFound(manuscript_id)

        snapshot = self._reader.get_snapshot(str(valid_id.value))
        if snapshot is None:
            raise ManuscriptNotFound(manuscript_id)

        draft = history.current_draft.name
        if branch_name is not None and branch_name != draft:
            raise RevisionError(
                f"Draft '{branch_name}' is not the current draft. Switch to it before committing."
            )

        revision = history.commit(draft, snapshot, message)
        self._repository.save(history)
        return revision
