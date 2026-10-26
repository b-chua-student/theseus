from uuid import UUID

from flask import Blueprint, current_app, jsonify, request
from flask.typing import ResponseReturnValue
from pydantic import ValidationError

from api.extensions import limiter
from api.schemas.manuscript_requests import CreateManuscriptRequest, UpdateManuscriptRequest
from api.schemas.manuscript_responses import ManuscriptResponseDTO
from services.manuscript.delete_manuscript import DeleteManuscriptService
from services.manuscript.get_all_manuscript import GetAllManuscriptService
from services.manuscript.update_manuscript import UpdateManuscriptService

manuscripts_bp = Blueprint("manuscripts", __name__)


@manuscripts_bp.post("/create")
@limiter.limit("5/minute")
def create_manuscript() -> ResponseReturnValue:
    """Validate the request and create a manuscript."""
    try:
        payload = CreateManuscriptRequest.model_validate(request.get_json(silent=True))
    except ValidationError:
        return jsonify({"error": "Provide a JSON object with a non-empty title."}), 400

    service = current_app.extensions["create_manuscript_service"]

    manuscript = service.execute(
        project_id=FakeManuscriptRepository.PROJECT_ID,
        title=payload.title,
    )

    response = ManuscriptResponseDTO.from_domain(manuscript)
    return jsonify(response.to_dict()), 201


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
    """Update an existing manuscript's title by its UUID.

    Args:
        manuscript_id: String representation of the manuscript UUID from the URL path.

    Returns:
        200 with the serialized updated manuscript, 400 on invalid UUID or JSON
        payload, or 404 if the manuscript does not exist.
    """
    try:
        parsed_id = UUID(manuscript_id)
    except ValueError:
        return jsonify({"error": "Invalid manuscript ID format."}), 400

    raw_body = request.get_json(silent=True)
    if not isinstance(raw_body, dict):
        return jsonify({"error": "Request body must be a valid JSON object."}), 400

    try:
        validated_body = UpdateManuscriptRequest.model_validate(raw_body)
    except ValidationError as err:
        return jsonify({"error": err.errors()}), 400

    update_manuscript_service: UpdateManuscriptService = current_app.extensions[
        "update_manuscript_service"
    ]

    try:
        updated_manuscript = update_manuscript_service.execute(
            manuscript_id=parsed_id,
            title=validated_body.title,
        )
    except ValueError as err:
        return jsonify({"error": str(err)}), 404

    response_dto = ManuscriptResponseDTO.from_domain(updated_manuscript)
    return jsonify(response_dto.to_dict()), 200


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
    get_all_service: GetAllManuscriptService = current_app.extensions["get_all_manuscripts_service"]
    manuscripts = get_all_service.execute()
    response_data = [ManuscriptResponseDTO.from_domain(m).to_dict() for m in manuscripts]
    return jsonify(response_data), 200
