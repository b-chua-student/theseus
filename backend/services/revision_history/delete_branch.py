from uuid import UUID

from domain.revision_history.entities import Branch
from repositories.revision_history.revision_history_repository import RevisionHistoryRepository


class DeleteBranchService:
    def __init__(
        self,
        revision_history_repo: RevisionHistoryRepository,
    ) -> None:
        self._revision_history_repo = revision_history_repo

    def execute(
        self,
        manuscript_id: UUID,
        branch_name: str,
    ) -> None:
        history = self._revision_history_repo.get_by_manuscript_id(manuscript_id)

        if history is None:
            raise ValueError("Revision history not found")

        history.delete_branch(branch_name)
        self._revision_history_repo.save(history)
