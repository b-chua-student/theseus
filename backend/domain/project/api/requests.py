from pydantic import BaseModel, EmailStr, Field


class CreateProjectRequest(BaseModel):
    project_name: str = Field(min_length=1, max_length=50)


class RenameProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class EditProjectDescriptionRequest(BaseModel):
    description: str = Field(min_length=1)


class TransferProjectOwnershipRequest(BaseModel):
    new_owner_id: str = Field(min_length=1)
