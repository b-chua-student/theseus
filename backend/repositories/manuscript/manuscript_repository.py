from abc import ABC, abstractmethod
from domain.manuscript.aggregates import Manuscript
from uuid import UUID


class ManuscriptRepository(ABC):
    @abstractmethod
    def save(self, manuscript: Manuscript) -> None:
        pass

    @abstractmethod
    def get_by_id(self, manuscript_id: UUID) -> Manuscript | None:
        pass

    @abstractmethod
    def get_by_project_id(self, project_id: UUID) -> list[Manuscript]:
        pass

    @abstractmethod
    def get_all(self) -> list[Manuscript]:
        pass

    @abstractmethod
    def delete(self, manuscript_id: UUID) -> None:
        pass

    @abstractmethod
    def exists(self, manuscript_id: UUID) -> bool:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass
