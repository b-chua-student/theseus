from uuid import UUID

from flask import Blueprint, current_app, jsonify, request
from flask.typing import ResponseReturnValue
from pydantic import ValidationError

from api.extensions import limiter
from api.schemas.manuscript_requests import (
    CreateManuscriptRequest,
    UpdateManuscriptRequest,
    UpdateSectionRequest,
)
from api.schemas.conversation_requests import (
    AskQuestionRequest
)
from api.schemas.manuscript_responses import ManuscriptResponseDTO
from api.schemas.conversation_responses import (
    ExchangeResponseDTO,
)
from services.manuscript.delete_manuscript import DeleteManuscriptService
from services.manuscript.get_all_manuscript import GetAllManuscriptService
from services.manuscript.update_manuscript import UpdateManuscriptService
from services.manuscript.update_section import UpdateSectionService
from services.indexing.index_manuscript_service import IndexManuscriptService
from services.conversation.ask_question import AskQuestionService
from ports.generation.errors import GenerationError, GenerationTimeoutError

manuscripts_bp = Blueprint("manuscripts", __name__)


def _parse_url_ids(user_id: str, project_id: str) -> tuple[UUID, UUID] | tuple[None, None]:
    """Parse and validate the user_id and project_id path parameters.

    Returns:
        A (user_uuid, project_uuid) tuple on success, or (None, None) if either
        value is not a valid UUID.
    """
    try:
        return UUID(user_id), UUID(project_id)
    except ValueError:
        return None, None


@manuscripts_bp.get("")
def list_manuscripts(user_id: str, project_id: str) -> ResponseReturnValue:
    """Retrieve all manuscripts for a project.

    Args:
        user_id: String representation of the owner user UUID from the URL path.
        project_id: String representation of the project UUID from the URL path.

    Returns:
        200 with a list of serialized manuscripts, or 400 on invalid UUIDs.
    """
    parsed_user_id, parsed_project_id = _parse_url_ids(user_id, project_id)
    if parsed_user_id is None:
        return jsonify({"error": "Invalid user_id or project_id format."}), 400

    get_all_service: GetAllManuscriptService = current_app.extensions["get_all_manuscripts_service"]
    manuscripts = get_all_service.execute(project_id=parsed_project_id)
    response_data = [ManuscriptResponseDTO.from_domain(m).to_dict() for m in manuscripts]
    return jsonify(response_data), 200


@manuscripts_bp.post("")
@limiter.limit("5/minute")
def create_manuscript(user_id: str, project_id: str) -> ResponseReturnValue:
    """Validate the request and create a manuscript under a project.

    Args:
        user_id: String representation of the owner user UUID from the URL path.
        project_id: String representation of the project UUID from the URL path.

    Returns:
        201 with the serialized manuscript, or 400 on invalid input.
    """
    parsed_user_id, parsed_project_id = _parse_url_ids(user_id, project_id)
    if parsed_user_id is None:
        return jsonify({"error": "Invalid user_id or project_id format."}), 400

    raw_body = request.get_json(silent=True)
    if not isinstance(raw_body, dict):
        return jsonify({"error": "Request body must be a valid JSON object."}), 400

    try:
        payload = CreateManuscriptRequest.model_validate(raw_body)
    except ValidationError as err:
        return jsonify({"error": err.errors()}), 400

    service = current_app.extensions["create_manuscript_service"]
    manuscript = service.execute(project_id=parsed_project_id, title=payload.title)

    return jsonify(ManuscriptResponseDTO.from_domain(manuscript).to_dict()), 201


@manuscripts_bp.get("/<manuscript_id>")
def get_manuscript(user_id: str, project_id: str, manuscript_id: str) -> ResponseReturnValue:
    """Retrieve a single manuscript by its UUID.

    Args:
        user_id: String representation of the owner user UUID from the URL path.
        project_id: String representation of the project UUID from the URL path.
        manuscript_id: String representation of the manuscript UUID from the URL path.

    Returns:
        200 with the serialized manuscript, 400 on invalid UUID, or 404 if not found.
    """
    parsed_user_id, parsed_project_id = _parse_url_ids(user_id, project_id)
    if parsed_user_id is None:
        return jsonify({"error": "Invalid user_id or project_id format."}), 400

    try:
        parsed_manuscript_id = UUID(manuscript_id)
    except ValueError:
        return jsonify({"error": "Invalid manuscript ID format."}), 400

    service = current_app.extensions["get_manuscript_service"]

    try:
        manuscript = service.execute(parsed_manuscript_id)
    except ValueError as err:
        return jsonify({"error": str(err)}), 404

    return jsonify(ManuscriptResponseDTO.from_domain(manuscript).to_dict()), 200


@manuscripts_bp.patch("/<manuscript_id>")
@limiter.limit("10/hour")
def update_manuscript(user_id: str, project_id: str, manuscript_id: str) -> ResponseReturnValue:
    """Update an existing manuscript's title by its UUID.

    Args:
        user_id: String representation of the owner user UUID from the URL path.
        project_id: String representation of the project UUID from the URL path.
        manuscript_id: String representation of the manuscript UUID from the URL path.

    Returns:
        200 with the serialized updated manuscript, 400 on invalid UUID or JSON
        payload, or 404 if the manuscript does not exist.
    """
    parsed_user_id, parsed_project_id = _parse_url_ids(user_id, project_id)
    if parsed_user_id is None:
        return jsonify({"error": "Invalid user_id or project_id format."}), 400

    try:
        parsed_manuscript_id = UUID(manuscript_id)
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
            manuscript_id=parsed_manuscript_id,
            title=validated_body.title,
        )
    except ValueError as err:
        return jsonify({"error": str(err)}), 404

    return jsonify(ManuscriptResponseDTO.from_domain(updated_manuscript).to_dict()), 200


@manuscripts_bp.delete("/<manuscript_id>")
@limiter.limit("10/hour")
def delete_manuscript(user_id: str, project_id: str, manuscript_id: str) -> ResponseReturnValue:
    """Delete a manuscript by its UUID.

    Args:
        user_id: String representation of the owner user UUID from the URL path.
        project_id: String representation of the project UUID from the URL path.
        manuscript_id: String representation of the manuscript UUID from the URL path.

    Returns:
        204 No Content on success, 400 if the UUID is invalid, or 404 if not found.
    """
    parsed_user_id, parsed_project_id = _parse_url_ids(user_id, project_id)
    if parsed_user_id is None:
        return jsonify({"error": "Invalid user_id or project_id format."}), 400

    try:
        parsed_manuscript_id = UUID(manuscript_id)
    except ValueError:
        return jsonify({"error": "Invalid manuscript ID format."}), 400

    delete_manuscript_service: DeleteManuscriptService = current_app.extensions[
        "delete_manuscript_service"
    ]

    try:
        delete_manuscript_service.execute(parsed_manuscript_id)
    except ValueError as err:
        return jsonify({"error": str(err)}), 404

    return "", 204


@manuscripts_bp.patch("/<manuscript_id>/sections/<section_id>")
@limiter.limit("30/minute")
def update_section(
    user_id: str, project_id: str, manuscript_id: str, section_id: str
) -> ResponseReturnValue:
    """Update an existing section's heading and/or body.

    Args:
        user_id: String representation of the owner user UUID from the URL path.
        project_id: String representation of the project UUID from the URL path.
        manuscript_id: String representation of the manuscript UUID from the URL path.
        section_id: String representation of the section UUID from the URL path.

    Returns:
        200 with the serialized updated manuscript, 400 on invalid UUID or
        JSON payload, or 404 if the manuscript or section does not exist.
    """
    parsed_user_id, parsed_project_id = _parse_url_ids(user_id, project_id)
    if parsed_user_id is None:
        return jsonify({"error": "Invalid user_id or project_id format."}), 400

    try:
        parsed_manuscript_id = UUID(manuscript_id)
        parsed_section_id = UUID(section_id)
    except ValueError:
        return jsonify({"error": "Invalid manuscript_id or section_id format."}), 400

    raw_body = request.get_json(silent=True)
    if not isinstance(raw_body, dict):
        return jsonify({"error": "Request body must be a valid JSON object."}), 400

    try:
        payload = UpdateSectionRequest.model_validate(raw_body)
    except ValidationError as err:
        return jsonify({"error": err.errors()}), 400

    if payload.heading is None and payload.body is None:
        return jsonify({"error": "At least one of 'heading' or 'body' must be provided."}), 400

    service: UpdateSectionService = current_app.extensions["update_section_service"]

    try:
        updated_manuscript = service.execute(
            manuscript_id=parsed_manuscript_id,
            section_id=parsed_section_id,
            heading=payload.heading,
            body=payload.body,
        )
    except ValueError as err:
        return jsonify({"error": str(err)}), 404

    return jsonify(ManuscriptResponseDTO.from_domain(updated_manuscript).to_dict()), 200


@manuscripts_bp.post("/<manuscript_id>/chunk")
@limiter.limit("5/minute")
def chunk(user_id: str, project_id: str, manuscript_id: str) -> ResponseReturnValue:
    try:
        validated_manuscript_id = UUID(manuscript_id)
    except ValueError:
        return jsonify(error="Invalid manuscript id"), 400

    service: IndexManuscriptService = current_app.extensions["index_manuscript_service"]

    try:
        indexed = service.execute(validated_manuscript_id)
    except ValueError:
        return jsonify(error="Manuscript not found"), 404
    except Exception:
        current_app.logger.exception("Indexing failed")
        return jsonify(error="Indexing failed"), 500

    return jsonify(
        indexed_document_id=str(indexed.indexed_document_id.value),
        status=indexed.status.value,
        chunk_count=len(indexed.chunks),
    ), 200


@manuscripts_bp.post("/<manuscript_id>/ask")
@limiter.limit("10/minute")
def ask(user_id: str, project_id: str, manuscript_id: str) -> ResponseReturnValue:
    try:
        validated_manuscript_id = UUID(manuscript_id)
    except ValueError:
        return jsonify(error="Invalid manuscript id"), 400

    try:
        payload = AskQuestionRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return jsonify(error="Invalid request", details=exc.errors(include_url=False)), 400

    service: AskQuestionService = current_app.extensions["ask_question_service"]

    try:
        exchange = service.execute(validated_manuscript_id, payload.content)
    except GenerationTimeoutError:
        current_app.logger.warning("Generation timed out")
        return jsonify(error="The assistant timed out. Try again."), 504
    except GenerationError:
        current_app.logger.exception("Generation failed")
        return jsonify(error="The assistant is unavailable."), 502
    except ValueError as exc:
        return jsonify(error=str(exc)), 409
    except Exception:
        current_app.logger.exception("Ask failed")
        return jsonify(error="Failed to answer question"), 500

    return jsonify(ExchangeResponseDTO.from_domain(exchange).to_dict()), 200
