from abc import ABC, abstractmethod

from domain.src_lib.models.aggregates import Source
from domain.src_lib.models.value_objects import SourceId


class SourceRepository(ABC):
    """Port for persisting and retrieving sources."""

    @abstractmethod
    def get(self, source_id: SourceId) -> Source | None:
        """Return the source with this ID, or None if it does not exist."""
        ...

    @abstractmethod
    def list_active(self) -> list[Source]:
        """Return all sources that have not been removed."""
        ...

    @abstractmethod
    def save(self, source: Source) -> None:
        """Insert or update a source."""
        ...
