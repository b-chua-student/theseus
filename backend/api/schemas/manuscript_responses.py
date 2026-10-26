from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from domain.manuscript.aggregates import Manuscript
from domain.manuscript.entities import Section


@dataclass(frozen=True)
class SectionResponseDTO:
    """Immutable response DTO representing a single manuscript section.

    Attributes:
        id: Unique identifier of the section.
        parent_id: Identifier of the parent section, or None for top-level.
        heading: Section heading text.
        body: Section body text.
        ordinal: Zero-based position among siblings.
    """

    id: UUID
    parent_id: UUID | None
    heading: str
    body: str
    ordinal: int

    @classmethod
    def from_domain(cls, section: Section) -> SectionResponseDTO:
        """Build a DTO from a domain section.

        Args:
            section: Section entity to convert.

        Returns:
            DTO populated from the section, with value objects unwrapped
            to plain strings.
        """
        return cls(
            id=section.id,
            parent_id=section.parent_id,
            heading=section.heading.value,
            body=section.body.value,
            ordinal=section.ordinal,
        )

    def to_dict(self) -> dict:
        """Serialize the DTO to a JSON-compatible dictionary.

        Returns:
            Dictionary with UUIDs converted to strings. ``parent_id`` is
            None for top-level sections.
        """
        return {
            "id": str(self.id),
            "parent_id": str(self.parent_id) if self.parent_id is not None else None,
            "heading": self.heading,
            "body": self.body,
            "ordinal": self.ordinal,
        }


@dataclass(frozen=True)
class ManuscriptResponseDTO:
    """Immutable response DTO representing a manuscript.

    Attributes:
        id: Unique identifier of the manuscript.
        project_id: ID of the project the manuscript belongs to.
        title: Title of the manuscript.
        sections: Ordered list of sections within the manuscript.
    """

    id: UUID
    project_id: UUID
    title: str
    sections: tuple[SectionResponseDTO, ...] = field(default_factory=tuple)

    @classmethod
    def from_domain(
        cls,
        manuscript: Manuscript,
    ) -> ManuscriptResponseDTO:
        """Build a DTO from a domain manuscript.

        Sections are sorted with top-level sections first, then by ordinal.

        Args:
            manuscript: Manuscript aggregate to convert.

        Returns:
            DTO populated from the manuscript and its sections.
        """
        sections = tuple(
            sorted(
                (SectionResponseDTO.from_domain(s) for s in manuscript.sections),
                key=lambda s: (s.parent_id is not None, s.ordinal),
            )
        )
        return cls(
            id=manuscript.id,
            project_id=manuscript.project_id,
            title=manuscript.title,
            sections=sections,
        )

    def to_dict(self) -> dict:
        """Serialize the DTO to a JSON-compatible dictionary.

        Returns:
            Dictionary with UUIDs converted to strings and sections
            serialized via ``SectionResponseDTO.to_dict``.
        """
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "title": self.title,
            "sections": [s.to_dict() for s in self.sections],
        }
