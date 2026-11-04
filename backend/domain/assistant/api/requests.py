from pydantic import BaseModel, Field, field_validator


class AskRequest(BaseModel):
    """Request body for asking the assistant a question."""

    query: str = Field(min_length=1, max_length=4000)

    @field_validator("query")
    @classmethod
    def not_blank(cls, value: str) -> str:
        """Reject queries that are empty or whitespace only."""
        if not value.strip():
            raise ValueError("Query must not be blank.")
        return value
