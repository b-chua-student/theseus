from dataclasses import dataclass
from uuid import UUID

from .value_objects import Body, Heading


@dataclass(eq=False)
class Section:
    """A section within a manuscript, optionally nested under a parent.

    Attributes:
        id: Unique identifier of the section.
        parent_id: Identifier of the parent section, or None if top-level.
        heading: The section's heading.
        body: The section's body content.
        ordinal: Zero-based position of the section among its siblings.
    """

    id: UUID
    parent_id: UUID | None
    heading: Heading
    body: Body
    ordinal: int

    def __post_init__(self) -> None:
        """Validate the section after initialization.

        Raises:
            ValueError: If ordinal is negative.
        """
        if self.ordinal < 0:
            raise ValueError("Section ordinal cannot be negative")

    def rename(self, heading: Heading) -> None:
        """Change the section's heading.

        Args:
            heading: The new heading.
        """
        self.heading = heading

    def edit_body(self, body: Body) -> None:
        """Replace the section's body content.

        Args:
            body: The new body.
        """
        self.body = body
