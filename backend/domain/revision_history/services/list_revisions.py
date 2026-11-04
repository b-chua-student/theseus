from domain.revision_history.infrastructure.ports.revision_history_repository import (
    RevisionHistoryRepository,
)
from domain.revision_history.models.entities import Revision
from domain.revision_history.models.value_objects import ManuscriptId

from .errors import (
    HistoryNotFound,
)


class ListRevisionsService:
    """Use case: list a draft's revisions, newest first."""

    def __init__(self, repository: RevisionHistoryRepository) -> None:
        self._repository = repository

    def execute(self, manuscript_id: str, branch_name: str | None = None) -> list[Revision]:
        """Return revisions of the named draft (default: current draft), newest first.

        Raises:
            HistoryNotFound: if the manuscript has no revision history.
        """
        history = self._repository.get_by_manuscript_id(ManuscriptId.from_str(manuscript_id))
        if history is None:
            raise HistoryNotFound(manuscript_id)

        return list(
            reversed(
                (
                    history.get_branch(branch_name) if branch_name else history.current_draft
                ).revisions
            )
        )
