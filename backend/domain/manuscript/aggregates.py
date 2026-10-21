from uuid import UUID, uuid4

from .entities import Section
from .value_objects import Heading, Body


class Manuscript:
    """Aggregate root for a manuscript and its hierarchy of sections.

    Sections form a tree. Each section has a parent (or None for top level)
    and an ordinal that is its zero-based position among its siblings.
    All mutations go through this class to keep ordinals contiguous and
    the tree acyclic.
    """

    def __init__(
        self,
        id: UUID,
        project_id: UUID,
        title: str,
    ) -> None:
        """Create a manuscript.

        Args:
            id: Unique identifier of the manuscript.
            project_id: Identifier of the owning project.
            title: Manuscript title. Surrounding whitespace is stripped.

        Raises:
            ValueError: If the title is empty or whitespace only.
        """
        if not title.strip():
            raise ValueError("Manuscript title cannot be empty")

        self._id = id
        self._project_id = project_id
        self._title = title.strip()
        self._sections: dict[UUID, Section] = {}

    @property
    def id(self) -> UUID:
        """Unique identifier of the manuscript."""
        return self._id

    @property
    def project_id(self) -> UUID:
        """Identifier of the project that owns the manuscript."""
        return self._project_id

    @property
    def title(self) -> str:
        """Current manuscript title."""
        return self._title

    @property
    def sections(self) -> tuple[Section, ...]:
        """Copies of all sections, in insertion order.

        Returned sections are detached copies; mutating them does not
        affect the manuscript.
        """
        return tuple(
            Section(
                id=section.id,
                parent_id=section.parent_id,
                heading=section.heading,
                body=section.body,
                ordinal=section.ordinal,
            )
            for section in self._sections.values()
        )

    def rename(self, title: str) -> None:
        """Change the manuscript title.

        Args:
            title: New title. Surrounding whitespace is stripped.

        Raises:
            ValueError: If the title is empty or whitespace only.
        """
        title = title.strip()

        if not title:
            raise ValueError("Manuscript title cannot be empty")

        self._title = title

    def add_section(
        self,
        heading: str,
        body: str = "",
        parent_id: UUID | None = None,
        ordinal: int | None = None,
    ) -> Section:
        """Add a new section.

        Args:
            heading: Section heading text.
            body: Section body text.
            parent_id: Parent section id, or None for a top-level section.
            ordinal: Position among siblings. Defaults to the end.
                Existing siblings at or after this position shift down.

        Returns:
            The newly created section.

        Raises:
            ValueError: If the parent does not exist or the ordinal is out
                of range.
        """
        if parent_id is not None:
            if parent_id not in self._sections:
                raise ValueError("Parent section does not exist")

        siblings = [
            section
            for section in self._sections.values()
            if section.parent_id == parent_id
        ]

        if ordinal is None:
            ordinal = len(siblings)

        if ordinal < 0 or ordinal > len(siblings):
            raise ValueError("Invalid section ordinal")

        for sibling in siblings:
            if sibling.ordinal >= ordinal:
                sibling.ordinal += 1

        section = Section(
            id=uuid4(),
            parent_id=parent_id,
            heading=Heading(heading),
            body=Body(body),
            ordinal=ordinal,
        )

        self._sections[section.id] = section
        return section

    def get_section(self, section_id: UUID) -> Section:
        """Return a copy of a section.

        Args:
            section_id: Id of the section to fetch.

        Returns:
            A detached copy of the section.

        Raises:
            ValueError: If the section does not exist.
        """
        try:
            section = self._sections[section_id]
        except KeyError:
            raise ValueError("Section does not exist") from None

        return Section(
            id=section.id,
            parent_id=section.parent_id,
            heading=section.heading,
            body=section.body,
            ordinal=section.ordinal,
        )

    def edit_section(
        self,
        section_id: UUID,
        heading: str | None = None,
        body: str | None = None,
    ) -> None:
        """Update a section's heading and/or body.

        Arguments left as None are unchanged.

        Args:
            section_id: Id of the section to edit.
            heading: New heading text.
            body: New body text.

        Raises:
            ValueError: If the section does not exist.
        """
        section = self._get_section(section_id)

        if heading is not None:
            section.rename(Heading(heading))

        if body is not None:
            section.edit_body(Body(body))

    def remove_section(self, section_id: UUID) -> None:
        """Remove a section and all of its descendants.

        Remaining siblings are re-numbered to stay contiguous.

        Args:
            section_id: Id of the section to remove.

        Raises:
            ValueError: If the section does not exist.
        """
        self._get_section(section_id)

        descendants = self._get_descendant_ids(section_id)
        to_remove = descendants | {section_id}

        parent_id = self._sections[section_id].parent_id

        for target_id in to_remove:
            del self._sections[target_id]

        siblings = sorted(
            (
                section
                for section in self._sections.values()
                if section.parent_id == parent_id
            ),
            key=lambda section: section.ordinal,
        )

        for ordinal, sibling in enumerate(siblings):
            sibling.ordinal = ordinal

    def reorder_section(
        self,
        section_id: UUID,
        new_ordinal: int,
    ) -> None:
        """Move a section to a new position among its current siblings.

        Args:
            section_id: Id of the section to move.
            new_ordinal: Target zero-based position.

        Raises:
            ValueError: If the section does not exist or the ordinal is
                out of range.
        """
        section = self._get_section(section_id)

        siblings = sorted(
            (
                item
                for item in self._sections.values()
                if item.parent_id == section.parent_id
            ),
            key=lambda item: item.ordinal,
        )

        if new_ordinal < 0 or new_ordinal >= len(siblings):
            raise ValueError("Invalid section ordinal")

        siblings.remove(section)
        siblings.insert(new_ordinal, section)

        for ordinal, sibling in enumerate(siblings):
            sibling.ordinal = ordinal

    def move_section(
        self,
        section_id: UUID,
        new_parent_id: UUID | None,
        new_ordinal: int | None = None,
    ) -> None:
        """Move a section, with its subtree, under a different parent.

        Ordinals of both the old and new sibling groups are re-numbered.

        Args:
            section_id: Id of the section to move.
            new_parent_id: Id of the new parent, or None for top level.
            new_ordinal: Position among the new siblings. Defaults to the
                end.

        Raises:
            ValueError: If the section or new parent does not exist, the
                section would become its own parent or a descendant's
                child, or the ordinal is out of range.
        """
        section = self._get_section(section_id)

        if new_parent_id is not None:
            self._get_section(new_parent_id)

        if new_parent_id == section_id:
            raise ValueError("A section cannot be its own parent")

        if new_parent_id in self._get_descendant_ids(section_id):
            raise ValueError("Moving section would create a cycle")

        old_parent_id = section.parent_id

        old_siblings = sorted(
            (
                item
                for item in self._sections.values()
                if item.parent_id == old_parent_id
                and item.id != section_id
            ),
            key=lambda item: item.ordinal,
        )

        for ordinal, sibling in enumerate(old_siblings):
            sibling.ordinal = ordinal

        new_siblings = sorted(
            (
                item
                for item in self._sections.values()
                if item.parent_id == new_parent_id
                and item.id != section_id
            ),
            key=lambda item: item.ordinal,
        )

        if new_ordinal is None:
            new_ordinal = len(new_siblings)

        if new_ordinal < 0 or new_ordinal > len(new_siblings):
            raise ValueError("Invalid section ordinal")

        new_siblings.insert(new_ordinal, section)

        section.parent_id = new_parent_id

        for ordinal, sibling in enumerate(new_siblings):
            sibling.ordinal = ordinal

    def _get_section(self, section_id: UUID) -> Section:
        try:
            return self._sections[section_id]
        except KeyError:
            raise ValueError("Section does not exist") from None

    def _get_descendant_ids(self, section_id: UUID) -> set[UUID]:
        descendants: set[UUID] = set()
        pending = [section_id]

        while pending:
            current_id = pending.pop()

            children = [
                section.id
                for section in self._sections.values()
                if section.parent_id == current_id
            ]

            for child_id in children:
                if child_id not in descendants:
                    descendants.add(child_id)
                    pending.append(child_id)

        return descendants
