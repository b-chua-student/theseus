from pydantic import BaseModel, ConfigDict, Field


class AskQuestionRequest(BaseModel):
    """Request payload for asking a question about a manuscript."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    content: str = Field(min_length=1)
