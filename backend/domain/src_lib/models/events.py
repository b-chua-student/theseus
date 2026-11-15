from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from .value_objects import SourceId


@dataclass(frozen=True)
class SourceAdded:
    """Domain event raised when a source is added to a project."""

    source_id: SourceId
    project_id: UUID
    file_ref: str | None
    kind: Literal["file", "text"] = "file"  # Default for backward compatibility


@dataclass(frozen=True)
class SourceUpdated:
    """Domain event raised when a text source is updated."""

    source_id: SourceId
    project_id: UUID
    kind: Literal["text"]
    version: int


@dataclass(frozen=True)
class SourceRemoved:
    """Domain event raised when a source is removed from a project."""

    source_id: SourceId
    project_id: UUID
