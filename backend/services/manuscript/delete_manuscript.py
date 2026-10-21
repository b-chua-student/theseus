from uuid import UUID

from repositories.manuscript.manuscript_repository import ManuscriptRepository


class DeleteManuscriptService:
    def __init__(self, repository: ManuscriptRepository) -> None:
        self._repository = repository

    def execute(self, manuscript_id: UUID) -> None:
        manuscript = self._repository.get_by_id(manuscript_id)

        if manuscript is None:
            raise ValueError("Manuscript not found")

        self._repository.delete(manuscript_id)
