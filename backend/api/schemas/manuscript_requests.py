from pydantic import BaseModel, ConfigDict, Field


class CreateManuscriptRequest(BaseModel):
    """Request payload for creating a manuscript.

    Unknown fields are rejected and surrounding whitespace is stripped
    from string values.

    Attributes:
        title: Title of the manuscript. Must be non-empty.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=1)
