from uuid import UUID

from flask import Blueprint, current_app, jsonify, request
from flask.typing import ResponseReturnValue
from pydantic import ValidationError

from api.extensions import limiter
from api.schemas.project_requests import CreateProjectRequest, UpdateProjectRequest
from api.schemas.project_responses import ProjectResponseDTO
from services.project.delete_project import DeleteProjectService
from services.project.get_all_projects import GetAllProjectsService
from services.project.get_project import GetProjectService
from services.project.update_project import UpdateProjectService

projects_bp = Blueprint("projects", __name__)


@projects_bp.post("")
@limiter.limit("5/minute")
def create_project() -> ResponseReturnValue:
    """Validate the request and create a project.

    Returns:
        201 with the serialized project, or 400 on invalid input.
    """
    raw_body = request.get_json(silent=True)
    if not isinstance(raw_body, dict):
        return jsonify({"error": "Request body must be a valid JSON object."}), 400

    try:
        payload = CreateProjectRequest.model_validate(raw_body)
    except ValidationError as err:
        return jsonify({"error": err.errors()}), 400

    try:
        owner_id = UUID(payload.owner_id)
    except ValueError:
        return jsonify({"error": "Invalid owner_id format."}), 400

    service = current_app.extensions["create_project_service"]
    project = service.execute(owner_id=owner_id, name=payload.name)

    response = ProjectResponseDTO.from_domain(project)
    return jsonify(response.to_dict()), 201


@projects_bp.get("")
def list_projects() -> ResponseReturnValue:
    """Retrieve all projects.

    Returns:
        200 with a list of serialized projects.
    """
    service: GetAllProjectsService = current_app.extensions["get_all_projects_service"]
    projects = service.execute()
    return jsonify([ProjectResponseDTO.from_domain(p).to_dict() for p in projects]), 200


@projects_bp.get("/<project_id>")
def get_project(project_id: str) -> ResponseReturnValue:
    """Retrieve a single project by its UUID.

    Args:
        project_id: String representation of the project UUID from the URL path.

    Returns:
        200 with the serialized project, 400 on invalid UUID, or 404 if not found.
    """
    try:
        parsed_id = UUID(project_id)
    except ValueError:
        return jsonify({"error": "Invalid project ID format."}), 400

    service: GetProjectService = current_app.extensions["get_project_service"]

    try:
        project = service.execute(parsed_id)
    except ValueError as err:
        return jsonify({"error": str(err)}), 404

    return jsonify(ProjectResponseDTO.from_domain(project).to_dict()), 200


@projects_bp.patch("/<project_id>")
@limiter.limit("10/hour")
def update_project(project_id: str) -> ResponseReturnValue:
    """Update an existing project's name by its UUID.

    Args:
        project_id: String representation of the project UUID from the URL path.

    Returns:
        200 with the serialized updated project, 400 on invalid UUID or JSON
        payload, or 404 if the project does not exist.
    """
    try:
        parsed_id = UUID(project_id)
    except ValueError:
        return jsonify({"error": "Invalid project ID format."}), 400

    raw_body = request.get_json(silent=True)
    if not isinstance(raw_body, dict):
        return jsonify({"error": "Request body must be a valid JSON object."}), 400

    try:
        validated_body = UpdateProjectRequest.model_validate(raw_body)
    except ValidationError as err:
        return jsonify({"error": err.errors()}), 400

    service: UpdateProjectService = current_app.extensions["update_project_service"]

    try:
        project = service.execute(project_id=parsed_id, name=validated_body.name)
    except ValueError as err:
        return jsonify({"error": str(err)}), 404

    return jsonify(ProjectResponseDTO.from_domain(project).to_dict()), 200


@projects_bp.delete("/<project_id>")
@limiter.limit("10/hour")
def delete_project(project_id: str) -> ResponseReturnValue:
    """Delete a project by its UUID.

    Args:
        project_id: String representation of the project UUID from the URL path.

    Returns:
        204 No Content on success, 400 if the UUID is invalid, or 404 if not found.
    """
    try:
        parsed_id = UUID(project_id)
    except ValueError:
        return jsonify({"error": "Invalid project ID format."}), 400

    service: DeleteProjectService = current_app.extensions["delete_project_service"]

    try:
        service.execute(parsed_id)
    except ValueError as err:
        return jsonify({"error": str(err)}), 404

    return "", 204
