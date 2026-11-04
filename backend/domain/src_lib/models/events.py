from dataclasses import dataclass
from uuid import UUID

from .value_objects import SourceId


@dataclass(frozen=True)
class SourceAdded:
    """Domain event raised when a source is added to a project."""

    source_id: SourceId
    project_id: UUID
    file_ref: str


@dataclass(frozen=True)
class SourceRemoved:
    """Domain event raised when a source is removed from a project."""

    source_id: SourceId
    project_id: UUID
