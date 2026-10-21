from uuid import UUID

from domain.manuscript.aggregates import Manuscript
from repositories.manuscript.manuscript_repository import ManuscriptRepository


class GetManuscriptService:
    def __init__(self, repository: ManuscriptRepository) -> None:
        self._repository = repository

    def execute(self, manuscript_id: UUID) -> Manuscript:
        manuscript = self._repository.get_by_id(manuscript_id)

        if manuscript is None:
            raise ValueError("Manuscript not found")

        return manuscript
