from uuid import UUID

from flask import Blueprint, current_app, jsonify
from flask.typing import ResponseReturnValue

from api.extensions import limiter
from api.schemas.manuscript_responses import ManuscriptResponseDTO
from services.manuscript.delete_manuscript import DeleteManuscriptService
from services.manuscript.get_all_manuscript import GetAllManuscriptService


manuscripts_bp = Blueprint("manuscripts", __name__)


@manuscripts_bp.post("/create")
@limiter.limit("5/minute")
def create_manuscript() -> ResponseReturnValue:
    """Create docstring."""
    # TODO: Parse and validate JSON body.
    # TODO: Return 400 on invalid input.
    # TODO: Resolve project_id (replace hardcoded value).
    # TODO: Call create_manuscript_service.
    # TODO: Return serialized manuscript with 201.
    return "", 501


@manuscripts_bp.get("/<manuscript_id>")
def get_manuscript(manuscript_id: str) -> ResponseReturnValue:
    """Create docstring."""
    # TODO: Validate manuscript_id as UUID (400 on failure).
    # TODO: Call get_manuscript_service.
    # TODO: Return 404 if not found.
    # TODO: Serialize via response DTO instead of inline dict.
    return "", 501


@manuscripts_bp.patch("/<manuscript_id>")
@limiter.limit("10/hour")
def update_manuscript(manuscript_id: str) -> ResponseReturnValue:
    """Create docstring."""
    # TODO: Validate manuscript_id as UUID (400 on failure).
    # TODO: Parse and validate JSON body (request schema).
    # TODO: Call update_manuscript_service.
    # TODO: Return 404 if not found.
    # TODO: Return updated manuscript.
    return "", 501


@manuscripts_bp.delete("/<manuscript_id>")
@limiter.limit("10/hour")
def delete_manuscript(manuscript_id: str) -> ResponseReturnValue:
    """Delete a manuscript by its UUID.

    Args:
        manuscript_id: String representation of the manuscript UUID from the URL path.

    Returns:
        204 No Content on success, 400 if the UUID is invalid, or 404 if not found.
    """
    try:
        parsed_id = UUID(manuscript_id)
    except ValueError:
        return jsonify({"error": "Invalid manuscript ID format."}), 400

    delete_manuscript_service: DeleteManuscriptService = current_app.extensions[
        "delete_manuscript_service"
    ]

    try:
        delete_manuscript_service.execute(parsed_id)
    except ValueError as err:
        return jsonify({"error": str(err)}), 404

    return "", 204


@manuscripts_bp.get("")
def list_manuscripts() -> ResponseReturnValue:
    """Retrieve all manuscripts."""
    get_all_service: GetAllManuscriptService = current_app.extensions["get_all_manuscript_service"]
    manuscripts = get_all_service.execute()
    response_data = [ManuscriptResponseDTO.from_domain(m).to_dict() for m in manuscripts]
    return jsonify(response_data), 200
