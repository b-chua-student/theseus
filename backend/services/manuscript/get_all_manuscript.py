from domain.manuscript.aggregates import Manuscript
from repositories.manuscript.manuscript_repository import ManuscriptRepository


class GetAllManuscriptService:
    def __init__(self, repository: ManuscriptRepository) -> None:
        self._repository = repository

    def execute(self) -> list[Manuscript]:
        return self._repository.get_all()
