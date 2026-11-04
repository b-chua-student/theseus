from flask import Blueprint, current_app, jsonify, request
from flask.typing import ResponseReturnValue
from pydantic import ValidationError

from domain.identity.api.auth.routes import login_required

from .errors import SourceNotFoundError
from .requests import AddSourceRequest, UpdateSourceMetadataRequest

source_bp = Blueprint("source_library", __name__)


@source_bp.get("")
@login_required
def list_sources() -> ResponseReturnValue:
    """List all sources in the library."""
    container = current_app.extensions["container"]

    sources = container.source.list.execute()

    return jsonify(
        [
            dict(
                id=str(s.id.value),
                title=s.title.value,
                authors=[a.name for a in s.authors],
                year=s.year,
                file_ref=s.file_ref,
            )
            for s in sources
        ]
    ), 200


@source_bp.post("")
@login_required
def add_source() -> ResponseReturnValue:
    """Add a source and return its new ID."""
    try:
        body = AddSourceRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as e:
        return jsonify(
            error="Invalid request", details=e.errors(include_url=False, include_context=False)
        ), 400

    container = current_app.extensions["container"]

    source_id = container.source.add.execute(
        title=body.title,
        authors=body.authors,
        year=body.year,
        file_ref=body.file_ref,
        project_id=body.project_id,
    )

    return jsonify(id=str(source_id.value)), 201


@source_bp.get("/<source_id>")
@login_required
def get_source(source_id: str) -> ResponseReturnValue:
    """Fetch a single source, or respond with not-found."""
    container = current_app.extensions["container"]

    source = container.source.get.execute(source_id=source_id)

    if source is None:
        raise SourceNotFoundError(f"Source '{source_id}' not found")

    return jsonify(
        id=str(source.id.value),
        title=source.title.value,
        authors=[a.name for a in source.authors],
        year=source.year,
        file_ref=source.file_ref,
    ), 200


@source_bp.delete("/<source_id>")
@login_required
def remove_source(source_id: str) -> ResponseReturnValue:
    """Remove a source, or respond with not-found."""
    container = current_app.extensions["container"]

    source = container.source.get.execute(source_id=source_id)

    if source is None:
        raise SourceNotFoundError(f"Source '{source_id}' not found")

    container.source.remove.execute(source_id=source_id)

    return "", 204


@source_bp.patch("/<source_id>/metadata")
@login_required
def update_source_metadata(source_id: str) -> ResponseReturnValue:
    """Replace a source's title, authors and year."""
    try:
        body = UpdateSourceMetadataRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as e:
        return jsonify(
            error="Invalid request", details=e.errors(include_url=False, include_context=False)
        ), 400

    container = current_app.extensions["container"]

    source = container.source.get.execute(source_id=source_id)

    if source is None:
        raise SourceNotFoundError(f"Source '{source_id}' not found")

    container.source.update_metadata.execute(
        source_id=source_id,
        title=body.title,
        authors=body.authors,
        year=body.year,
    )

    return "", 204
