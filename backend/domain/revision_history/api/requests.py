from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class CommitRevisionRequest(BaseModel):
    """Request body for committing a new revision to a manuscript."""

    message: str = Field(min_length=1, max_length=256)
    branch: str | None = Field(default=None, min_length=1, max_length=64)


class RestoreRevisionRequest(BaseModel):
    """Request body for restoring a manuscript to a prior revision."""

    branch: str | None = Field(default=None, min_length=1, max_length=64)


class CreateDraftRequest(BaseModel):
    """Request body for creating a new draft, optionally from a past revision."""

    name: str = Field(min_length=1, max_length=64)
    from_revision_id: str | None = None


class RenameDraftRequest(BaseModel):
    """Request body for renaming an existing draft."""

    name: str = Field(min_length=1, max_length=64)


class ResolutionRequest(BaseModel):
    """Choose a draft side for a conflict on a section or field."""

    section_id: UUID
    field: Literal["heading", "body", "parent_id", "ordinal", "section"]
    choice: Literal["target", "source"]


class MergeDraftRequest(BaseModel):
    """Request body for merging a draft into the current draft."""

    message: str | None = Field(default=None, min_length=1, max_length=256)
    resolutions: list[ResolutionRequest] = Field(default_factory=list, max_length=1000)

    @model_validator(mode="after")
    def unique_resolutions(self) -> Self:
        """Reject multiple resolutions for the same section and field."""
        keys = [(r.section_id, r.field) for r in self.resolutions]
        if len(set(keys)) != len(keys):
            raise ValueError("Duplicate merge resolutions")
        return self
