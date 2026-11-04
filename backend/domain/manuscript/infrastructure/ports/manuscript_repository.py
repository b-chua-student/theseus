from abc import ABC, abstractmethod

from domain.manuscript.models.aggregates import Manuscript
from domain.manuscript.models.value_objects import ManuscriptId, ProjectId


class ManuscriptRepository(ABC):
    """Port for persisting and querying Manuscript aggregates."""

    @abstractmethod
    def save(self, manuscript: Manuscript) -> None:
        """Insert the manuscript, or replace the stored one with the same id."""

    @abstractmethod
    def get_by_id(self, manuscript_id: ManuscriptId) -> Manuscript | None:
        """Return the manuscript with the given id, or None if absent."""

    @abstractmethod
    def get_all(self) -> list[Manuscript]:
        """Return all stored manuscripts."""

    @abstractmethod
    def list_by_project_id(self, project_id: ProjectId) -> list[Manuscript]:
        """Return the manuscripts belonging to the given project."""

    @abstractmethod
    def delete(self, manuscript_id: ManuscriptId) -> None:
        """Remove the manuscript with the given id, if present."""

    @abstractmethod
    def exists(self, manuscript_id: ManuscriptId) -> bool:
        """Return whether a manuscript with the given id is stored."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all stored manuscripts."""
