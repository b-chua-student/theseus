from pydantic import BaseModel, Field


class CreateManuscriptRequest(BaseModel):
    """Request body for creating a manuscript, optionally from a template."""

    title: str = Field(min_length=1, max_length=256)
    template: bool = False


class RenameManuscriptRequest(BaseModel):
    """Request body for renaming a manuscript."""

    title: str = Field(min_length=1, max_length=256)


class AppendSectionRequest(BaseModel):
    """Request body for appending a section, optionally under a parent section."""

    heading: str = Field(min_length=1, max_length=128)
    parent_id: str | None = None


class RenameSectionRequest(BaseModel):
    """Request body for renaming a section heading."""

    heading: str = Field(min_length=1, max_length=128)


class EditSectionBodyRequest(BaseModel):
    """Request body for replacing a section's body text."""

    body: str
