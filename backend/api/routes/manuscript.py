from flask import Blueprint, current_app, jsonify, request
from flask.typing import ResponseReturnValue
from pydantic import ValidationError

from api.extensions import limiter
from api.schemas.manuscript_requests import CreateManuscriptRequest
from api.schemas.manuscript_responses import ManuscriptResponseDTO
from repositories.manuscript.fake_manuscript_repository import (
    FakeManuscriptRepository,
)

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
    """Create docstring."""
    # TODO: Validate manuscript_id as UUID (400 on failure).
    # TODO: Call delete_manuscript_service.
    # TODO: Return 404 if not found.
    # TODO: Return 204 on success.
    return "", 501


@manuscripts_bp.get("")
def list_manuscripts() -> ResponseReturnValue:
    """Create docstring."""
    # TODO: Call get_all_manuscripts_service.
    # TODO: Move ManuscriptResponse to schemas module (BaseModel import was missing).
    # TODO: Serialize and return list with 200.
    return "", 501
