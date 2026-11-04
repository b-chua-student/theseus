from dataclasses import dataclass

from .value_objects import Heading, SectionId


@dataclass(eq=False)
class Section:
    """A heading and body of text within a manuscript, optionally nested under a parent."""

    id: SectionId
    parent_id: SectionId | None
    heading: Heading
    ordinal: int
    body: str = ""

    def __post_init__(self) -> None:
        if self.ordinal < 0:
            raise ValueError("Section ordinal cannot be negative")

    def rename(self, heading: Heading) -> None:
        """Replace the section heading."""
        self.heading = heading

    def edit_body(self, body: str) -> None:
        """Replace the section body."""
        self.body = body
