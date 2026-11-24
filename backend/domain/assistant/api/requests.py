from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from domain.assistant.models.value_objects import ExchangeContext


class AskRequest(BaseModel):
    """Request body for asking the assistant a question."""

    context_scope: Literal["none", "manuscript", "source_library"] = "source_library"
    source_ids: list[UUID] | None = Field(default=None, max_length=1000)
    manuscript_text: str = Field(default="", max_length=500_000)
    quote: str | None = Field(default=None, max_length=20_000)
    query: str = Field(min_length=1, max_length=4000)

    @field_validator("query")
    @classmethod
    def not_blank(cls, value: str) -> str:
        """Reject queries that are empty or whitespace only."""
        if not value.strip():
            raise ValueError("Query must not be blank.")
        return value

    def context(self) -> ExchangeContext:
        """Decode the legacy scope and fields into independent exchange inputs."""
        return ExchangeContext.decode(
            self.context_scope,
            manuscript_text=self.manuscript_text,
            source_ids=[str(value) for value in self.source_ids]
            if self.source_ids is not None
            else None,
            quote=self.quote,
        )
