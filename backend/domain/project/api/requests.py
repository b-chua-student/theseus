from pydantic import BaseModel, Field


class CreateProjectRequest(BaseModel):
    """Request body for creating a project; name must be 1-50 characters."""

    project_name: str = Field(min_length=1, max_length=50)


class RenameProjectRequest(BaseModel):
    """Request body for renaming a project; name must be 1-50 characters."""

    name: str = Field(min_length=1, max_length=50)


class EditProjectDescriptionRequest(BaseModel):
    """Request body for setting a project description; must be non-empty."""

    description: str = Field(min_length=1)


class TransferProjectOwnershipRequest(BaseModel):
    """Request body for transferring ownership; new owner ID must be non-empty."""

    new_owner_id: str = Field(min_length=1)
