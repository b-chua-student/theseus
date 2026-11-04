from pydantic import BaseModel, Field


class CommitRevisionRequest(BaseModel):
    """Request body for committing a new revision to a manuscript."""

    message: str = Field(min_length=1, max_length=256)
    branch: str | None = Field(default=None, min_length=1, max_length=64)


class RestoreRevisionRequest(BaseModel):
    """Request body for restoring a manuscript to a prior revision."""

    branch: str | None = Field(default=None, min_length=1, max_length=64)


class CreateDraftRequest(BaseModel):
    """Request body for creating a new draft, optionally from a past revision."""

    name: str = Field(min_length=1, max_length=64)
    from_revision_id: str | None = None


class RenameDraftRequest(BaseModel):
    """Request body for renaming an existing draft."""

    name: str = Field(min_length=1, max_length=64)
