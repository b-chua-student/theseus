from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AskRequest(BaseModel):
    """Request body for asking the assistant a question."""

    context_scope: Literal["none", "source_library"] = "source_library"
    source_ids: list[UUID] | None = Field(default=None, max_length=1000)
    query: str = Field(min_length=1, max_length=4000)

    @field_validator("query")
    @classmethod
    def not_blank(cls, value: str) -> str:
        """Reject queries that are empty or whitespace only."""
        if not value.strip():
            raise ValueError("Query must not be blank.")
        return value
