from uuid import UUID

from flask import Blueprint, jsonify, request, current_app
from application.schemas.manuscript_dto import ManuscriptResponseDTO
from pydantic import BaseModel, ConfigDict, ValidationError, Field

manuscripts_bp = Blueprint("manuscripts", __name__)

class CreateManuscriptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=1)

@manuscripts_bp.post("/create")
def create_manuscript():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "A JSON object is required"}), 400

    try:
        body = CreateManuscriptRequest.model_validate(data)
    except ValidationError as e:
        return jsonify({"error": e.errors(include_url=False, include_context=False)}), 400

    project_id = UUID("00000000-0000-0000-0000-000000000001")

    service = current_app.extensions["create_manuscript_service"]
    manuscript = service.execute(project_id=project_id, title=body.title)

    return jsonify(ManuscriptResponseDTO.from_domain(manuscript).to_dict()), 201

@manuscripts_bp.get("/<manuscript_id>")
def get_manuscript(manuscript_id: str):
    try:
        manuscript_uuid = UUID(manuscript_id)
    except ValueError:
        return jsonify({"error": "Invalid manuscript ID"}), 400

    service = current_app.extensions["get_manuscript_service"]

    try:
        manuscript = service.execute(manuscript_uuid)
    except ValueError:
        return jsonify({"error": "Manuscript not found"}), 404

    return jsonify(
        {
            "id": str(manuscript.id),
            "title": manuscript.title,
            "sections": [
                {
                    "id": str(s.id),
                    "parent_id": str(s.parent_id) if s.parent_id else None,
                    "heading": s.heading.value,
                    "body": s.body.value,
                    "ordinal": s.ordinal,
                }
                for s in manuscript.sections
            ],
        }
    ), 200

@manuscripts_bp.patch("/<manuscript_id>")
def update_manuscript(manuscript_id: str):
    try:
        manuscript_uuid = UUID(manuscript_id)
    except ValueError:
        return jsonify({"error": "Invalid manuscript ID"}), 400

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "A JSON object is required"}), 400

    title = data.get("title")

    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "A non-empty title is required"}), 400

    # TODO: Call an application service to load the manuscript,
    # rename it, and persist the updated aggregate.

    return jsonify(
        {
            "message": "Manuscript update not implemented",
            "manuscript_id": str(manuscript_uuid),
        }
    ), 501

@manuscripts_bp.delete("/<manuscript_id>")
def delete_manuscript(manuscript_id: str):
    try:
        manuscript_uuid = UUID(manuscript_id)
    except ValueError:
        return jsonify({"error": "Invalid manuscript ID"}), 400

    service = current_app.extensions["delete_manuscript_service"]

    try:
        service.execute(manuscript_uuid)
    except ValueError:
        return jsonify({"error": "Manuscript not found"}), 404

    return "", 204

class ManuscriptResponse(BaseModel):
    id: UUID
    title: str

@manuscripts_bp.get("")
def list_manuscripts():
    service = current_app.extensions["get_all_manuscripts_service"]
    manuscripts = service.execute()

    items = [
        ManuscriptResponse(id=m.id, title=m.title).model_dump(mode="json")
        for m in manuscripts
    ]
    return jsonify(items), 200
