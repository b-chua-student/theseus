from uuid import UUID

from pydantic import BaseModel, Field


class AddSourceRequest(BaseModel):
    """Request body for adding a source to a project."""

    title: str = Field(min_length=1, max_length=256)
    authors: list[str] | None = None
    year: int | None = None
    file_ref: str = Field(min_length=1)
    project_id: UUID


class UpdateSourceMetadataRequest(BaseModel):
    """Request body for replacing a source's title, authors and year."""

    title: str = Field(min_length=1, max_length=256)
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
