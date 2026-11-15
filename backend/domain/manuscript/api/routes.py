from flask import Blueprint, current_app, jsonify, request
from flask.typing import ResponseReturnValue
from pydantic import ValidationError

from domain.identity.api.auth.routes import login_required

from .errors import ManuscriptNotFoundError
from .requests import (
    AppendSectionRequest,
    CreateManuscriptRequest,
    EditSectionBodyRequest,
    RenameManuscriptRequest,
    RenameSectionRequest,
)

manuscript_bp = Blueprint("manuscript", __name__)


@manuscript_bp.get("")
@login_required
def list_manuscripts(project_id: str) -> ResponseReturnValue:
    """List all manuscripts belonging to the project."""
    container = current_app.extensions["container"]

    manuscripts = container.manuscript.list.execute(project_id=project_id)

    return jsonify(
        [
            dict(
                id=m.id,
                project_id=m.project_id,
                title=m.title,
            )
            for m in manuscripts
        ]
    ), 200


@manuscript_bp.post("")
@login_required
def create_manuscript(project_id: str) -> ResponseReturnValue:
    """Create a manuscript in the project, optionally from a template."""
    try:
        body = CreateManuscriptRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as e:
        return jsonify(
            error="Invalid request", details=e.errors(include_url=False, include_context=False)
        ), 400

    container = current_app.extensions["container"]

    manuscript = container.manuscript.create.execute(
        project_id=project_id,
        title=body.title,
        template=body.template,
    )

    return jsonify(id=str(manuscript.id.value)), 201


@manuscript_bp.get("/<manuscript_id>")
@login_required
def get_manuscript(project_id: str, manuscript_id: str) -> ResponseReturnValue:
    """Get a manuscript, with its working copy or latest committed revision content."""
    container = current_app.extensions["container"]

    manuscript = container.manuscript.get.execute(manuscript_id=manuscript_id)

    if manuscript is None:
        raise ManuscriptNotFoundError(f"Manuscript '{manuscript_id}' not found")

    # Content comes from the current draft's latest revision when history exists;
    # otherwise fall back to the manuscript's own sections. `?view=working` returns the
    # working copy (uncommitted edits included), which is what editing/saving operates on.
    snapshot = None
    if request.args.get("view") != "working":
        snapshot = container.revision_history.current_content.execute(manuscript_id=manuscript_id)
    if snapshot is not None:
        sections = [
            dict(
                id=str(s.id),
                parent_id=str(s.parent_id) if s.parent_id else None,
                heading=s.heading,
                ordinal=s.ordinal,
                body=s.body,
            )
            for s in snapshot.sections
        ]
    else:
        sections = [
            dict(
                id=str(s.id.value),
                parent_id=str(s.parent_id.value) if s.parent_id else None,
                heading=s.heading.value,
                ordinal=s.ordinal,
                body=s.body,
            )
            for s in manuscript.sections
        ]

    return jsonify(
        id=str(manuscript.id.value),
        project_id=str(manuscript.project_id.value),
        title=manuscript.title.value,
        sections=sections,
    ), 200


@manuscript_bp.delete("/<manuscript_id>")
@login_required
def delete_manuscript(project_id: str, manuscript_id: str) -> ResponseReturnValue:
    """Delete a manuscript by id."""
    container = current_app.extensions["container"]

    manuscript = container.manuscript.get.execute(manuscript_id=manuscript_id)

    if manuscript is None:
        raise ManuscriptNotFoundError(f"Manuscript '{manuscript_id}' not found")

    container.manuscript.delete.execute(manuscript_id=manuscript_id)

    return "", 204


@manuscript_bp.patch("/<manuscript_id>/title")
@login_required
def rename_manuscript(project_id: str, manuscript_id: str) -> ResponseReturnValue:
    """Rename a manuscript's title."""
    try:
        body = RenameManuscriptRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as e:
        return jsonify(
            error="Invalid request", details=e.errors(include_url=False, include_context=False)
        ), 400

    container = current_app.extensions["container"]

    manuscript = container.manuscript.get.execute(manuscript_id=manuscript_id)

    if manuscript is None:
        raise ManuscriptNotFoundError(f"Manuscript '{manuscript_id}' not found")

    container.manuscript.rename.execute(
        manuscript_id=manuscript_id,
        new_title=body.title,
    )

    return "", 204


@manuscript_bp.post("/<manuscript_id>/sections")
@login_required
def append_section(project_id: str, manuscript_id: str) -> ResponseReturnValue:
    """Append a new section to the manuscript, optionally under a parent section."""
    try:
        body = AppendSectionRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as e:
        return jsonify(
            error="Invalid request", details=e.errors(include_url=False, include_context=False)
        ), 400

    container = current_app.extensions["container"]

    manuscript = container.manuscript.get.execute(manuscript_id=manuscript_id)

    if manuscript is None:
        raise ManuscriptNotFoundError(f"Manuscript '{manuscript_id}' not found")

    container.manuscript.append_section.execute(
        manuscript_id=manuscript_id,
        parent_id=body.parent_id,
        heading=body.heading,
    )

    return "", 201


@manuscript_bp.delete("/<manuscript_id>/sections/<section_id>")
@login_required
def remove_section(project_id: str, manuscript_id: str, section_id: str) -> ResponseReturnValue:
    """Remove a section from the manuscript."""
    container = current_app.extensions["container"]

    manuscript = container.manuscript.get.execute(manuscript_id=manuscript_id)

    if manuscript is None:
        raise ManuscriptNotFoundError(f"Manuscript '{manuscript_id}' not found")

    container.manuscript.remove_section.execute(
        manuscript_id=manuscript_id,
        section_id=section_id,
    )

    return "", 204


@manuscript_bp.patch("/<manuscript_id>/sections/<section_id>/heading")
@login_required
def rename_section(project_id: str, manuscript_id: str, section_id: str) -> ResponseReturnValue:
    """Rename a section's heading."""
    try:
        body = RenameSectionRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as e:
        return jsonify(
            error="Invalid request", details=e.errors(include_url=False, include_context=False)
        ), 400

    container = current_app.extensions["container"]

    manuscript = container.manuscript.get.execute(manuscript_id=manuscript_id)

    if manuscript is None:
        raise ManuscriptNotFoundError(f"Manuscript '{manuscript_id}' not found")

    container.manuscript.rename_section.execute(
        manuscript_id=manuscript_id,
        section_id=section_id,
        new_heading=body.heading,
    )

    return "", 204


@manuscript_bp.put("/<manuscript_id>/sections/<section_id>/body")
@login_required
def edit_section_body(project_id: str, manuscript_id: str, section_id: str) -> ResponseReturnValue:
    """Replace a section's body text."""
    try:
        body = EditSectionBodyRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as e:
        return jsonify(
            error="Invalid request", details=e.errors(include_url=False, include_context=False)
        ), 400

    container = current_app.extensions["container"]

    manuscript = container.manuscript.get.execute(manuscript_id=manuscript_id)

    if manuscript is None:
        raise ManuscriptNotFoundError(f"Manuscript '{manuscript_id}' not found")

    container.manuscript.edit_section_body.execute(
        manuscript_id=manuscript_id,
        section_id=section_id,
        body=body.body,
    )

    return "", 204
