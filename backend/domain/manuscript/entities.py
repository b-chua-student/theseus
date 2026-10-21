# backend/domain/manuscript/entities.py

from dataclasses import dataclass
from uuid import UUID

from .value_objects import Heading, Body


@dataclass(eq=False)
class Section:
    id: UUID
    parent_id: UUID | None
    heading: Heading
    body: Body
    ordinal: int

    def __post_init__(self) -> None:
        if self.ordinal < 0:
            raise ValueError("Section ordinal cannot be negative")

    def rename(self, heading: Heading) -> None:
        self.heading = heading

    def edit_body(self, body: Body) -> None:
        self.body = body
