from uuid import UUID

from flask import Blueprint, current_app, jsonify, request
from flask.typing import ResponseReturnValue
from pydantic import ValidationError

from api.extensions import limiter
from api.schemas.revision_history_requests import (
    AddMilestoneRequest,
    CommitRevisionRequest,
    CreateBranchRequest,
    InitializeHistoryRequest,
    MergeBranchesRequest,
    RestoreRevisionRequest,
)
from api.schemas.revision_history_responses import (
    BranchResponseDTO,
    MilestoneResponseDTO,
    RevisionHistoryResponseDTO,
    RevisionResponseDTO,
)
from domain.revision_history.exceptions import (
    BranchNotFoundError,
    DuplicateBranchError,
    DuplicateMilestoneError,
    InvalidRevisionError,
    MergeConflictError,
    MilestoneNotFoundError,
    RevisionNotFoundError,
)
from domain.revision_history.value_objects import MergeConflict

revision_histories_bp = Blueprint("revision_histories", __name__)


# ---------------------------------------------------------------------------
# Revision History (aggregate)
# ---------------------------------------------------------------------------


@revision_histories_bp.post("")
@limiter.limit("5/minute")
def initialize_history() -> ResponseReturnValue:
    """Initialize a new revision history for a manuscript.

    Returns:
        201 with the serialized history, or 400 on invalid input, or 409 if
        a history already exists for the manuscript.
    """
    raw_body = request.get_json(silent=True)
    if not isinstance(raw_body, dict):
        return jsonify({"error": "Request body must be a valid JSON object."}), 400

    try:
        payload = InitializeHistoryRequest.model_validate(raw_body)
    except ValidationError as err:
        return jsonify({"error": err.errors()}), 400

    try:
        project_id = UUID(payload.project_id)
        manuscript_id = UUID(payload.manuscript_id)
    except ValueError:
        return jsonify({"error": "Invalid UUID format in project_id or manuscript_id."}), 400

    service = current_app.extensions["initialize_history_service"]

    try:
        history = service.execute(
            project_id=project_id,
            manuscript_id=manuscript_id,
            tree_hash=payload.tree_hash,
            message=payload.message,
        )
    except ValueError as err:
        return jsonify({"error": str(err)}), 409
    except InvalidRevisionError as err:
        return jsonify({"error": str(err)}), 422

    return jsonify(RevisionHistoryResponseDTO.from_domain(history).to_dict()), 201


@revision_histories_bp.get("")
def list_histories() -> ResponseReturnValue:
    """Retrieve all revision histories.

    Returns:
        200 with a list of serialized revision histories.
    """
    service = current_app.extensions["get_all_histories_service"]
    histories = service.execute()
    return jsonify([RevisionHistoryResponseDTO.from_domain(h).to_dict() for h in histories]), 200


@revision_histories_bp.get("/<manuscript_id>")
def get_history(manuscript_id: str) -> ResponseReturnValue:
    """Retrieve the revision history for a manuscript.

    Args:
        manuscript_id: String representation of the manuscript UUID.

    Returns:
        200 with the serialized history, 400 on invalid UUID, or 404 if
        not found.
    """
    try:
        parsed_id = UUID(manuscript_id)
    except ValueError:
        return jsonify({"error": "Invalid manuscript ID format."}), 400

    service = current_app.extensions["get_history_service"]

    try:
        history = service.execute(parsed_id)
    except ValueError as err:
        return jsonify({"error": str(err)}), 404

    return jsonify(RevisionHistoryResponseDTO.from_domain(history).to_dict()), 200


@revision_histories_bp.delete("/<manuscript_id>")
@limiter.limit("10/hour")
def delete_history(manuscript_id: str) -> ResponseReturnValue:
    """Delete the revision history for a manuscript.

    Args:
        manuscript_id: String representation of the manuscript UUID.

    Returns:
        204 No Content on success, 400 on invalid UUID, or 404 if not found.
    """
    try:
        parsed_id = UUID(manuscript_id)
    except ValueError:
        return jsonify({"error": "Invalid manuscript ID format."}), 400

    service = current_app.extensions["delete_history_service"]

    try:
        service.execute(parsed_id)
    except ValueError as err:
        return jsonify({"error": str(err)}), 404

    return "", 204


# ---------------------------------------------------------------------------
# Revisions
# ---------------------------------------------------------------------------


@revision_histories_bp.get("/<manuscript_id>/revisions")
def list_revisions(manuscript_id: str) -> ResponseReturnValue:
    """List all revisions in the manuscript's history.

    Args:
        manuscript_id: String representation of the manuscript UUID.

    Returns:
        200 with a list of serialized revisions, 400 on invalid UUID, or
        404 if no history exists.
    """
    try:
        parsed_id = UUID(manuscript_id)
    except ValueError:
        return jsonify({"error": "Invalid manuscript ID format."}), 400

    service = current_app.extensions["get_history_service"]

    try:
        history = service.execute(parsed_id)
    except ValueError as err:
        return jsonify({"error": str(err)}), 404

    return jsonify([RevisionResponseDTO.from_domain(r).to_dict() for r in history.revisions]), 200


@revision_histories_bp.get("/<manuscript_id>/revisions/<revision_id>")
def get_revision(manuscript_id: str, revision_id: str) -> ResponseReturnValue:
    """Retrieve a single revision by its UUID.

    Args:
        manuscript_id: String representation of the manuscript UUID.
        revision_id: String representation of the revision UUID.

    Returns:
        200 with the serialized revision, 400 on invalid UUID, or 404 if
        the history or revision is not found.
    """
    try:
        parsed_manuscript_id = UUID(manuscript_id)
        parsed_revision_id = UUID(revision_id)
    except ValueError:
        return jsonify({"error": "Invalid UUID format."}), 400

    service = current_app.extensions["get_history_service"]

    try:
        history = service.execute(parsed_manuscript_id)
    except ValueError as err:
        return jsonify({"error": str(err)}), 404

    try:
        revision = history.get_revision(parsed_revision_id)
    except RevisionNotFoundError as err:
        return jsonify({"error": str(err)}), 404

    return jsonify(RevisionResponseDTO.from_domain(revision).to_dict()), 200


@revision_histories_bp.post("/<manuscript_id>/revisions")
@limiter.limit("10/minute")
def commit_revision(manuscript_id: str) -> ResponseReturnValue:
    """Commit a new revision on a branch.

    Args:
        manuscript_id: String representation of the manuscript UUID.

    Returns:
        201 with the serialized revision, 400 on invalid input, or 404 if
        the history or branch is not found.
    """
    try:
        parsed_id = UUID(manuscript_id)
    except ValueError:
        return jsonify({"error": "Invalid manuscript ID format."}), 400

    raw_body = request.get_json(silent=True)
    if not isinstance(raw_body, dict):
        return jsonify({"error": "Request body must be a valid JSON object."}), 400

    try:
        payload = CommitRevisionRequest.model_validate(raw_body)
    except ValidationError as err:
        return jsonify({"error": err.errors()}), 400

    service = current_app.extensions["commit_revision_service"]

    try:
        revision = service.execute(
            manuscript_id=parsed_id,
            branch_name=payload.branch_name,
            tree_hash=payload.tree_hash,
            message=payload.message,
        )
    except ValueError as err:
        return jsonify({"error": str(err)}), 404
    except BranchNotFoundError as err:
        return jsonify({"error": str(err)}), 404

    return jsonify(RevisionResponseDTO.from_domain(revision).to_dict()), 201


@revision_histories_bp.post("/<manuscript_id>/revisions/restore")
@limiter.limit("10/minute")
def restore_revision(manuscript_id: str) -> ResponseReturnValue:
    """Restore a previous revision's snapshot as a new commit on a branch.

    Args:
        manuscript_id: String representation of the manuscript UUID.

    Returns:
        201 with the serialized restore revision, 400 on invalid input, or
        404 if the history, branch, or target revision is not found.
    """
    try:
        parsed_id = UUID(manuscript_id)
    except ValueError:
        return jsonify({"error": "Invalid manuscript ID format."}), 400

    raw_body = request.get_json(silent=True)
    if not isinstance(raw_body, dict):
        return jsonify({"error": "Request body must be a valid JSON object."}), 400

    try:
        payload = RestoreRevisionRequest.model_validate(raw_body)
    except ValidationError as err:
        return jsonify({"error": err.errors()}), 400

    try:
        target_revision_id = UUID(payload.target_revision_id)
    except ValueError:
        return jsonify({"error": "Invalid target_revision_id format."}), 400

    service = current_app.extensions["restore_revision_service"]

    try:
        revision = service.execute(
            manuscript_id=parsed_id,
            branch_name=payload.branch_name,
            target_revision_id=target_revision_id,
            message=payload.message,
        )
    except ValueError as err:
        return jsonify({"error": str(err)}), 404
    except BranchNotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except RevisionNotFoundError as err:
        return jsonify({"error": str(err)}), 404

    return jsonify(RevisionResponseDTO.from_domain(revision).to_dict()), 201


# ---------------------------------------------------------------------------
# Branches
# ---------------------------------------------------------------------------


@revision_histories_bp.get("/<manuscript_id>/branches")
def list_branches(manuscript_id: str) -> ResponseReturnValue:
    """List all branches in the manuscript's history.

    Args:
        manuscript_id: String representation of the manuscript UUID.

    Returns:
        200 with a list of serialized branches, 400 on invalid UUID, or
        404 if no history exists.
    """
    try:
        parsed_id = UUID(manuscript_id)
    except ValueError:
        return jsonify({"error": "Invalid manuscript ID format."}), 400

    service = current_app.extensions["get_history_service"]

    try:
        history = service.execute(parsed_id)
    except ValueError as err:
        return jsonify({"error": str(err)}), 404

    return jsonify([BranchResponseDTO.from_domain(b).to_dict() for b in history.branches]), 200


@revision_histories_bp.get("/<manuscript_id>/branches/<branch_name>")
def get_branch(manuscript_id: str, branch_name: str) -> ResponseReturnValue:
    """Retrieve a branch by name.

    Args:
        manuscript_id: String representation of the manuscript UUID.
        branch_name: Name of the branch.

    Returns:
        200 with the serialized branch, 400 on invalid UUID, or 404 if
        the history or branch is not found.
    """
    try:
        parsed_id = UUID(manuscript_id)
    except ValueError:
        return jsonify({"error": "Invalid manuscript ID format."}), 400

    service = current_app.extensions["get_history_service"]

    try:
        history = service.execute(parsed_id)
    except ValueError as err:
        return jsonify({"error": str(err)}), 404

    try:
        branch = history.get_branch(branch_name)
    except BranchNotFoundError as err:
        return jsonify({"error": str(err)}), 404

    return jsonify(BranchResponseDTO.from_domain(branch).to_dict()), 200


@revision_histories_bp.get("/<manuscript_id>/branches/<branch_name>/head")
def get_branch_head(manuscript_id: str, branch_name: str) -> ResponseReturnValue:
    """Retrieve the head revision of a branch.

    Args:
        manuscript_id: String representation of the manuscript UUID.
        branch_name: Name of the branch.

    Returns:
        200 with the serialized head revision, 400 on invalid UUID, or
        404 if the history, branch, or head revision is not found.
    """
    try:
        parsed_id = UUID(manuscript_id)
    except ValueError:
        return jsonify({"error": "Invalid manuscript ID format."}), 400

    service = current_app.extensions["get_history_service"]

    try:
        history = service.execute(parsed_id)
    except ValueError as err:
        return jsonify({"error": str(err)}), 404

    try:
        revision = history.get_branch_head(branch_name)
    except (BranchNotFoundError, RevisionNotFoundError) as err:
        return jsonify({"error": str(err)}), 404

    return jsonify(RevisionResponseDTO.from_domain(revision).to_dict()), 200


@revision_histories_bp.post("/<manuscript_id>/branches")
@limiter.limit("10/hour")
def create_branch(manuscript_id: str) -> ResponseReturnValue:
    """Create a new branch in the revision history.

    Args:
        manuscript_id: String representation of the manuscript UUID.

    Returns:
        201 with the serialized branch, 400 on invalid input, 404 if the
        history or base revision is not found, or 409 if the branch name
        is already taken.
    """
    try:
        parsed_id = UUID(manuscript_id)
    except ValueError:
        return jsonify({"error": "Invalid manuscript ID format."}), 400

    raw_body = request.get_json(silent=True)
    if not isinstance(raw_body, dict):
        return jsonify({"error": "Request body must be a valid JSON object."}), 400

    try:
        payload = CreateBranchRequest.model_validate(raw_body)
    except ValidationError as err:
        return jsonify({"error": err.errors()}), 400

    from_revision_id = None
    if payload.from_revision_id is not None:
        try:
            from_revision_id = UUID(payload.from_revision_id)
        except ValueError:
            return jsonify({"error": "Invalid from_revision_id format."}), 400

    service = current_app.extensions["create_branch_service"]

    try:
        branch = service.execute(
            manuscript_id=parsed_id,
            name=payload.name,
            from_revision_id=from_revision_id,
        )
    except ValueError as err:
        return jsonify({"error": str(err)}), 400
    except DuplicateBranchError as err:
        return jsonify({"error": str(err)}), 409
    except (BranchNotFoundError, RevisionNotFoundError) as err:
        return jsonify({"error": str(err)}), 404
    except InvalidRevisionError as err:
        return jsonify({"error": str(err)}), 422

    return jsonify(BranchResponseDTO.from_domain(branch).to_dict()), 201


@revision_histories_bp.delete("/<manuscript_id>/branches/<branch_name>")
@limiter.limit("10/hour")
def delete_branch(manuscript_id: str, branch_name: str) -> ResponseReturnValue:
    """Delete a branch from the revision history.

    The ``main`` branch cannot be deleted.

    Args:
        manuscript_id: String representation of the manuscript UUID.
        branch_name: Name of the branch to delete.

    Returns:
        204 No Content on success, 400 on invalid UUID or attempt to delete
        ``main``, or 404 if the history or branch is not found.
    """
    try:
        parsed_id = UUID(manuscript_id)
    except ValueError:
        return jsonify({"error": "Invalid manuscript ID format."}), 400

    service = current_app.extensions["delete_branch_service"]

    try:
        service.execute(manuscript_id=parsed_id, branch_name=branch_name)
    except ValueError as err:
        return jsonify({"error": str(err)}), 404
    except InvalidRevisionError as err:
        return jsonify({"error": str(err)}), 400
    except BranchNotFoundError as err:
        return jsonify({"error": str(err)}), 404

    return "", 204


# ---------------------------------------------------------------------------
# Milestones
# ---------------------------------------------------------------------------


@revision_histories_bp.get("/<manuscript_id>/milestones")
def list_milestones(manuscript_id: str) -> ResponseReturnValue:
    """List all milestones in the manuscript's history.

    Args:
        manuscript_id: String representation of the manuscript UUID.

    Returns:
        200 with a list of serialized milestones, 400 on invalid UUID, or
        404 if no history exists.
    """
    try:
        parsed_id = UUID(manuscript_id)
    except ValueError:
        return jsonify({"error": "Invalid manuscript ID format."}), 400

    service = current_app.extensions["get_history_service"]

    try:
        history = service.execute(parsed_id)
    except ValueError as err:
        return jsonify({"error": str(err)}), 404

    return (
        jsonify([MilestoneResponseDTO.from_domain(m).to_dict() for m in history.milestones]),
        200,
    )


@revision_histories_bp.get("/<manuscript_id>/milestones/<milestone_name>")
def get_milestone(manuscript_id: str, milestone_name: str) -> ResponseReturnValue:
    """Retrieve a milestone by name.

    Args:
        manuscript_id: String representation of the manuscript UUID.
        milestone_name: Name of the milestone.

    Returns:
        200 with the serialized milestone, 400 on invalid UUID, or 404 if
        the history or milestone is not found.
    """
    try:
        parsed_id = UUID(manuscript_id)
    except ValueError:
        return jsonify({"error": "Invalid manuscript ID format."}), 400

    service = current_app.extensions["get_history_service"]

    try:
        history = service.execute(parsed_id)
    except ValueError as err:
        return jsonify({"error": str(err)}), 404

    try:
        milestone = history.get_milestone(milestone_name)
    except MilestoneNotFoundError as err:
        return jsonify({"error": str(err)}), 404

    return jsonify(MilestoneResponseDTO.from_domain(milestone).to_dict()), 200


@revision_histories_bp.post("/<manuscript_id>/milestones")
@limiter.limit("10/hour")
def add_milestone(manuscript_id: str) -> ResponseReturnValue:
    """Add a named milestone pointing to a revision.

    Args:
        manuscript_id: String representation of the manuscript UUID.

    Returns:
        201 with the serialized milestone, 400 on invalid input, 404 if
        the history or revision is not found, or 409 if the name is taken.
    """
    try:
        parsed_id = UUID(manuscript_id)
    except ValueError:
        return jsonify({"error": "Invalid manuscript ID format."}), 400

    raw_body = request.get_json(silent=True)
    if not isinstance(raw_body, dict):
        return jsonify({"error": "Request body must be a valid JSON object."}), 400

    try:
        payload = AddMilestoneRequest.model_validate(raw_body)
    except ValidationError as err:
        return jsonify({"error": err.errors()}), 400

    try:
        revision_id = UUID(payload.revision_id)
    except ValueError:
        return jsonify({"error": "Invalid revision_id format."}), 400

    service = current_app.extensions["add_milestone_service"]

    try:
        milestone = service.execute(
            manuscript_id=parsed_id,
            name=payload.name,
            revision_id=revision_id,
        )
    except ValueError as err:
        return jsonify({"error": str(err)}), 404
    except DuplicateMilestoneError as err:
        return jsonify({"error": str(err)}), 409
    except RevisionNotFoundError as err:
        return jsonify({"error": str(err)}), 404

    return jsonify(MilestoneResponseDTO.from_domain(milestone).to_dict()), 201


# ---------------------------------------------------------------------------
# Merges
# ---------------------------------------------------------------------------


@revision_histories_bp.post("/<manuscript_id>/merges")
@limiter.limit("5/minute")
def merge_branches(manuscript_id: str) -> ResponseReturnValue:
    """Merge the source branch into the target branch.

    Args:
        manuscript_id: String representation of the manuscript UUID.

    Returns:
        201 with the serialized merge revision, 400 on invalid input,
        404 if the history or a branch is not found, 409 if there are
        unresolved conflicts, or 422 if source and target are the same.
    """
    try:
        parsed_id = UUID(manuscript_id)
    except ValueError:
        return jsonify({"error": "Invalid manuscript ID format."}), 400

    raw_body = request.get_json(silent=True)
    if not isinstance(raw_body, dict):
        return jsonify({"error": "Request body must be a valid JSON object."}), 400

    try:
        payload = MergeBranchesRequest.model_validate(raw_body)
    except ValidationError as err:
        return jsonify({"error": err.errors()}), 400

    # Parse conflict section IDs.
    try:
        conflicts = tuple(
            MergeConflict(
                section_id=UUID(c.section_id),
                base=c.base,
                ours=c.ours,
                theirs=c.theirs,
            )
            for c in payload.conflicts
        )
    except ValueError:
        return jsonify({"error": "Invalid section_id in conflicts."}), 400

    service = current_app.extensions["merge_branches_service"]

    try:
        revision = service.execute(
            manuscript_id=parsed_id,
            source_branch_name=payload.source_branch_name,
            target_branch_name=payload.target_branch_name,
            tree_hash=payload.tree_hash,
            message=payload.message,
            conflicts=conflicts,
        )
    except ValueError as err:
        return jsonify({"error": str(err)}), 404
    except BranchNotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except MergeConflictError as err:
        return jsonify({"error": str(err)}), 409
    except InvalidRevisionError as err:
        return jsonify({"error": str(err)}), 422

    return jsonify(RevisionResponseDTO.from_domain(revision).to_dict()), 201
