from pydantic import BaseModel, ConfigDict, Field


class CreateProjectRequest(BaseModel):
    """Request payload for creating a project.

    Unknown fields are rejected and surrounding whitespace is stripped
    from string values.

    Attributes:
        name: Name of the project. Must be non-empty.
        owner_id: UUID string of the owning user.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1)
    owner_id: str = Field(min_length=1)


class UpdateProjectRequest(BaseModel):
    """Request payload for updating a project.

    Unknown fields are rejected and surrounding whitespace is stripped
    from string values.

    Attributes:
        name: New name of the project. Must be non-empty.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1)
