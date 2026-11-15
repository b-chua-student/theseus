from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


MAX_TEXT_TITLE_LENGTH = 200
MAX_TEXT_CONTENT_LENGTH = 100_000
MAX_TEXT_DESCRIPTION_LENGTH = 1000
MAX_TEXT_TAGS = 10

ContentTypeName = Literal["documentation", "notes", "code", "other"]


class TextSourceRequest(BaseModel):
    """Request body shared by POST and PUT of a text source (R1, R2).

    `content` is kept verbatim (R10, N5); title, description and tags are trimmed.
    """

    title: str
    content: str
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    content_type: ContentTypeName = Field(default="other", alias="contentType")

    model_config = ConfigDict(populate_by_name=False)

    @field_validator("title")
    @classmethod
    def _title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title is required")
        if len(v) > MAX_TEXT_TITLE_LENGTH:
            raise ValueError(f"Title must be at most {MAX_TEXT_TITLE_LENGTH} characters")
        return v

    @field_validator("content")
    @classmethod
    def _content(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Content is required")
        if len(v) > MAX_TEXT_CONTENT_LENGTH:
            raise ValueError(f"Content must be at most {MAX_TEXT_CONTENT_LENGTH:,} characters")
        return v

    @field_validator("description")
    @classmethod
    def _description(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if len(v) > MAX_TEXT_DESCRIPTION_LENGTH:
            raise ValueError(
                f"Description must be at most {MAX_TEXT_DESCRIPTION_LENGTH} characters"
            )
        return v or None

    @field_validator("tags")
    @classmethod
    def _tags(cls, v: list[str]) -> list[str]:
        cleaned = list(dict.fromkeys(t.strip() for t in v if t.strip()))
        if len(cleaned) > MAX_TEXT_TAGS:
            raise ValueError(f"At most {MAX_TEXT_TAGS} tags are allowed")
        return cleaned
