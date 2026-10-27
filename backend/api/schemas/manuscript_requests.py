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


class UpdateManuscriptRequest(BaseModel):
    """Request payload for updating a manuscript.

    Unknown fields are rejected and surrounding whitespace is stripped
    from string values.

    Attributes:
        title: New title of the manuscript. Must be non-empty.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=1)


class UpdateSectionRequest(BaseModel):
    """Request payload for updating a section within a manuscript.

    Unknown fields are rejected and surrounding whitespace is stripped
    from string values. At least one of ``heading`` or ``body`` must be
    provided.

    Attributes:
        heading: New heading text. Optional; omit to leave unchanged.
        body: New body HTML text. Optional; omit to leave unchanged.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    heading: str | None = Field(default=None, min_length=1)
    body: str | None = Field(default=None)
