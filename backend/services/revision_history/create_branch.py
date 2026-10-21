from uuid import UUID

from domain.revision_history.entities import Branch
from repositories.revision_history.revision_history_repository import RevisionHistoryRepository

class CreateBranchService:
    def __init__(
        self,
        revision_history_repo: RevisionHistoryRepository,
    ) -> None:
        self._revision_history_repo = revision_history_repo

    def execute(
        self,
        manuscript_id: UUID,
        branch_name: str,
        revision_id: UUID | None = None,
    ) -> Branch:
        history = self._get_history(manuscript_id)

        branch = history.create_branch(
            name=branch_name,
            from_revision_id=revision_id,
        )

        self._revision_history_repo.save(history)
        return branch

    def _get_history(self, manuscript_id: UUID):
        history = self._revision_history_repo.get_by_manuscript_id(
            manuscript_id
        )

        if history is None:
            raise ValueError("Revision history not found")

        return history
