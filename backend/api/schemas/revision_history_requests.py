from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class InitializeHistoryRequest(BaseModel):
    """Request payload for initializing a manuscript's revision history.

    Attributes:
        project_id: UUID string of the owning project.
        manuscript_id: UUID string of the manuscript.
        tree_hash: Snapshot tree hash representing the initial manuscript state.
        message: Commit message for the initial revision.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    project_id: str = Field(min_length=1)
    manuscript_id: str = Field(min_length=1)
    tree_hash: str = Field(min_length=1)
    message: str = Field(min_length=1)


class CommitRevisionRequest(BaseModel):
    """Request payload for committing a new revision on a branch.

    Attributes:
        branch_name: Name of the branch to commit to.
        tree_hash: Snapshot tree hash representing the new manuscript state.
        message: Commit message describing the changes.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    branch_name: str = Field(min_length=1)
    tree_hash: str = Field(min_length=1)
    message: str = Field(min_length=1)


class RestoreRevisionRequest(BaseModel):
    """Request payload for restoring a previous revision on a branch.

    Attributes:
        branch_name: Name of the branch to restore on.
        target_revision_id: UUID string of the revision to restore.
        message: Commit message for the restore operation.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    branch_name: str = Field(min_length=1)
    target_revision_id: str = Field(min_length=1)
    message: str = Field(min_length=1)


class CreateBranchRequest(BaseModel):
    """Request payload for creating a new branch.

    Attributes:
        name: Name of the new branch.
        from_revision_id: Optional UUID string of the revision to start from.
            Defaults to the head of ``main`` when omitted.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1)
    from_revision_id: str | None = Field(default=None)


class AddMilestoneRequest(BaseModel):
    """Request payload for adding a milestone.

    Attributes:
        name: Name of the milestone.
        revision_id: UUID string of the revision to associate the milestone with.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1)
    revision_id: str = Field(min_length=1)


class MergeConflictRequest(BaseModel):
    """A single unresolved merge conflict.

    Attributes:
        section_id: UUID string of the conflicting section.
        base: Common ancestor content.
        ours: Content from the target branch.
        theirs: Content from the source branch.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    section_id: str = Field(min_length=1)
    base: str
    ours: str
    theirs: str


class MergeBranchesRequest(BaseModel):
    """Request payload for merging two branches.

    Attributes:
        source_branch_name: Name of the branch to merge from.
        target_branch_name: Name of the branch to merge into.
        tree_hash: Snapshot tree hash of the merged state.
        message: Commit message for the merge revision.
        conflicts: List of unresolved merge conflicts. Defaults to empty.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source_branch_name: str = Field(min_length=1)
    target_branch_name: str = Field(min_length=1)
    tree_hash: str = Field(min_length=1)
    message: str = Field(min_length=1)
    conflicts: list[MergeConflictRequest] = Field(default_factory=list)
