from flask import Blueprint
from flask.typing import ResponseReturnValue

from application.extensions import limiter

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
