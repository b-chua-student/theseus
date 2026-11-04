from domain.revision_history.infrastructure.ports.manuscript_writer import ManuscriptWriter
from domain.revision_history.infrastructure.ports.revision_history_repository import (
    RevisionHistoryRepository,
)
from domain.revision_history.models.entities import Revision
from domain.revision_history.models.errors import RevisionError
from domain.revision_history.models.value_objects import ManuscriptId, RevisionId

from .errors import HistoryNotFound


class RestoreRevisionService:
    """Use case: revert the manuscript to a past revision of the current draft."""

    def __init__(
        self,
        repository: RevisionHistoryRepository,
        writer: ManuscriptWriter,
    ) -> None:
        self._repository = repository
        self._writer = writer

    def execute(self, manuscript_id: str, branch_name: str | None, revision_id: str) -> Revision:
        """Restore a revision as a new commit and apply its snapshot to the manuscript.

        Raises:
            HistoryNotFound: if the manuscript has no revision history.
            RevisionError: if `branch_name` is not current or the revision is not on it.
        """
        valid_id = ManuscriptId.from_str(manuscript_id)

        history = self._repository.get_by_manuscript_id(valid_id)
        if history is None:
            raise HistoryNotFound(manuscript_id)

        draft = history.current_draft.name
        if branch_name is not None and branch_name != draft:
            raise RevisionError(
                f"Draft '{branch_name}' is not the current draft. Switch to it before restoring."
            )

        revision = history.restore(draft, RevisionId.from_str(revision_id))
        self._writer.apply_snapshot(str(valid_id.value), revision.snapshot)
        self._repository.save(history)
        return revision
