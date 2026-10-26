from pydantic import BaseModel, ConfigDict, Field


class CreateUserRequest(BaseModel):
    """Request payload for creating a user.

    Unknown fields are rejected and surrounding whitespace is stripped
    from string values.

    Attributes:
        email: Email address of the user. Must be non-empty.
        display_name: Display name of the user. Must be non-empty.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    email: str = Field(min_length=1)
    display_name: str = Field(min_length=1)


class UpdateUserRequest(BaseModel):
    """Request payload for updating a user.

    All fields are optional; at least one must be provided.
    Unknown fields are rejected and surrounding whitespace is stripped
    from string values.

    Attributes:
        display_name: New display name. Must be non-empty when provided.
        email: New email address. Must be non-empty when provided.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    display_name: str | None = Field(default=None, min_length=1)
    email: str | None = Field(default=None, min_length=1)
