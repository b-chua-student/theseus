from abc import ABC, abstractmethod
from uuid import UUID

from .entities import Section


class AbstractManuscript(ABC):
    """Contract for a manuscript and its hierarchy of sections.

    Sections form a tree. Each section has a parent (or None for top level)
    and an ordinal that is its zero-based position among its siblings.
    All mutations go through implementations of this class to keep ordinals
    contiguous and the tree acyclic.
    """

    @property
    @abstractmethod
    def id(self) -> UUID:
        """Unique identifier of the manuscript."""

    @property
    @abstractmethod
    def project_id(self) -> UUID:
        """Identifier of the project that owns the manuscript."""

    @property
    @abstractmethod
    def title(self) -> str:
        """Current manuscript title."""

    @property
    @abstractmethod
    def sections(self) -> tuple[Section, ...]:
        """Detached copies of all sections, in insertion order."""

    @abstractmethod
    def rename(self, title: str) -> None:
        """Change the manuscript title.

        Raises:
            ValueError: If the title is empty or whitespace only.
        """

    @abstractmethod
    def add_section(
        self,
        heading: str,
        body: str = "",
        parent_id: UUID | None = None,
        ordinal: int | None = None,
    ) -> Section:
        """Add a section. Ordinal defaults to the end; later siblings shift down.

        Raises:
            ValueError: If the parent does not exist or the ordinal is out of range.
        """

    @abstractmethod
    def get_section(self, section_id: UUID) -> Section:
        """Return a detached copy of a section.

        Raises:
            ValueError: If the section does not exist.
        """

    @abstractmethod
    def edit_section(
        self,
        section_id: UUID,
        heading: str | None = None,
        body: str | None = None,
    ) -> None:
        """Update heading and/or body. Arguments left as None are unchanged.

        Raises:
            ValueError: If the section does not exist.
        """

    @abstractmethod
    def remove_section(self, section_id: UUID) -> None:
        """Remove a section and its descendants; re-number remaining siblings.

        Raises:
            ValueError: If the section does not exist.
        """

    @abstractmethod
    def reorder_section(self, section_id: UUID, new_ordinal: int) -> None:
        """Move a section to a new position among its current siblings.

        Raises:
            ValueError: If the section does not exist or the ordinal is out of range.
        """

    @abstractmethod
    def move_section(
        self,
        section_id: UUID,
        new_parent_id: UUID | None,
        new_ordinal: int | None = None,
    ) -> None:
        """Move a section and its subtree under a different parent.

        Raises:
            ValueError: If the section or new parent does not exist, the move
                would create a cycle, or the ordinal is out of range.
        """
