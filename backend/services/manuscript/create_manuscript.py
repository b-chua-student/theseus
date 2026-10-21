from uuid import UUID, uuid4

from domain.manuscript.aggregates import Manuscript
from domain.revision_history.aggregates import RevisionHistory
from repositories.manuscript.manuscript_repository import ManuscriptRepository
from repositories.revision_history.revision_history_repository import RevisionHistoryRepository


class CreateManuscriptService:
    def __init__(
        self,
        manuscript_repo: ManuscriptRepository,
        revision_history_repo: RevisionHistoryRepository,
    ) -> None:
        self._manuscript_repo = manuscript_repo
        self._revision_history_repo = revision_history_repo

    def execute(
        self,
        project_id: UUID,
        title: str,
    ) -> Manuscript:
        manuscript = Manuscript(
            id=uuid4(),
            project_id=project_id,
            title=title,
        )

        revision_history = RevisionHistory(
            project_id=project_id,
            manuscript_id=manuscript.id,
        )

        self._manuscript_repo.save(manuscript)
        self._revision_history_repo.save(revision_history)

        return manuscript
