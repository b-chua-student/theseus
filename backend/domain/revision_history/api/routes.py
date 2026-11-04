from flask import Blueprint, current_app, jsonify, request
from flask.typing import ResponseReturnValue
from pydantic import ValidationError

from domain.identity.api.auth.routes import login_required
from domain.revision_history.models.entities import Branch, Revision
from domain.revision_history.models.errors import NoChangesError

from .requests import (
    CommitRevisionRequest,
    CreateDraftRequest,
    RenameDraftRequest,
    RestoreRevisionRequest,
)

revision_bp = Blueprint("revision_history", __name__)


def _summary(r: Revision) -> dict:
    return dict(
        id=str(r.id.value),
        message=r.message,
        created_at=r.created_at.isoformat(),
    )


def _detail(r: Revision) -> dict:
    return dict(
        **_summary(r),
        sections=[
            dict(
                id=str(s.id),
                parent_id=str(s.parent_id) if s.parent_id else None,
                heading=s.heading,
                ordinal=s.ordinal,
                body=s.body,
            )
            for s in r.snapshot.sections
        ],
    )


@revision_bp.post("/history")
@login_required
def start_revision_history(project_id: str, manuscript_id: str) -> ResponseReturnValue:
    """Initialize revision history tracking for a manuscript."""
    container = current_app.extensions["container"]

    container.revision_history.start.execute(manuscript_id=manuscript_id)

    return "", 201


@revision_bp.post("")
@login_required
def commit_revision(project_id: str, manuscript_id: str) -> ResponseReturnValue:
    """Commit the current draft content as a new revision on a branch."""
    try:
        body = CommitRevisionRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as e:
        return jsonify(
            error="Invalid request", details=e.errors(include_url=False, include_context=False)
        ), 400

    container = current_app.extensions["container"]

    try:
        revision = container.revision_history.commit.execute(
            manuscript_id=manuscript_id,
            branch_name=body.branch,
            message=body.message,
        )
    except NoChangesError as e:
        return jsonify(error=e.message, code=e.code), 409

    _, current = container.revision_history.list_drafts.execute(manuscript_id=manuscript_id)

    return jsonify(**_summary(revision), draft=current), 201


@revision_bp.get("")
@login_required
def list_revisions(project_id: str, manuscript_id: str) -> ResponseReturnValue:
    """List revisions for a manuscript, optionally filtered by branch."""
    container = current_app.extensions["container"]

    revisions = container.revision_history.list.execute(
        manuscript_id=manuscript_id,
        branch_name=request.args.get("branch"),
    )

    return jsonify([_summary(r) for r in revisions]), 200


@revision_bp.get("/<revision_id>")
@login_required
def get_revision(project_id: str, manuscript_id: str, revision_id: str) -> ResponseReturnValue:
    """Fetch a single revision with its full section snapshot."""
    container = current_app.extensions["container"]

    revision = container.revision_history.get.execute(
        manuscript_id=manuscript_id,
        revision_id=revision_id,
    )

    return jsonify(_detail(revision)), 200


@revision_bp.post("/<revision_id>/restore")
@login_required
def restore_revision(project_id: str, manuscript_id: str, revision_id: str) -> ResponseReturnValue:
    """Restore a branch's working content to the state of a past revision."""
    try:
        body = RestoreRevisionRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as e:
        return jsonify(
            error="Invalid request", details=e.errors(include_url=False, include_context=False)
        ), 400

    container = current_app.extensions["container"]

    revision = container.revision_history.restore.execute(
        manuscript_id=manuscript_id,
        branch_name=body.branch,
        revision_id=revision_id,
    )

    return jsonify(_summary(revision)), 200


draft_bp = Blueprint("drafts", __name__)


def _draft(d: Branch, *, current: bool) -> dict:
    return dict(
        name=d.name,
        is_current=current,
        head=_summary(d.head),
        revision_count=len(d.revisions),
    )


@draft_bp.post("")
@login_required
def create_draft(project_id: str, manuscript_id: str) -> ResponseReturnValue:
    """Create a new draft, optionally seeded from a past revision."""
    try:
        body = CreateDraftRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as e:
        return jsonify(
            error="Invalid request", details=e.errors(include_url=False, include_context=False)
        ), 400

    container = current_app.extensions["container"]

    draft = container.revision_history.create_draft.execute(
        manuscript_id=manuscript_id,
        name=body.name,
        from_revision_id=body.from_revision_id,
    )

    return jsonify(_draft(draft, current=False)), 201


@draft_bp.get("")
@login_required
def list_drafts(project_id: str, manuscript_id: str) -> ResponseReturnValue:
    """List all drafts for a manuscript, marking which one is current."""
    container = current_app.extensions["container"]

    drafts, current = container.revision_history.list_drafts.execute(manuscript_id=manuscript_id)

    return jsonify([_draft(d, current=d.name == current) for d in drafts]), 200


@draft_bp.get("/<name>")
@login_required
def get_draft(project_id: str, manuscript_id: str, name: str) -> ResponseReturnValue:
    """Fetch a single draft by name."""
    container = current_app.extensions["container"]

    draft, current = container.revision_history.get_draft.execute(
        manuscript_id=manuscript_id, name=name
    )

    return jsonify(_draft(draft, current=current)), 200


@draft_bp.patch("/<name>")
@login_required
def rename_draft(project_id: str, manuscript_id: str, name: str) -> ResponseReturnValue:
    """Rename an existing draft."""
    try:
        body = RenameDraftRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as e:
        return jsonify(
            error="Invalid request", details=e.errors(include_url=False, include_context=False)
        ), 400

    container = current_app.extensions["container"]

    draft = container.revision_history.rename_draft.execute(
        manuscript_id=manuscript_id, name=name, new_name=body.name
    )
    _, current = container.revision_history.get_draft.execute(
        manuscript_id=manuscript_id, name=draft.name
    )

    return jsonify(_draft(draft, current=current)), 200


@draft_bp.delete("/<name>")
@login_required
def delete_draft(project_id: str, manuscript_id: str, name: str) -> ResponseReturnValue:
    """Delete a draft by name."""
    container = current_app.extensions["container"]

    container.revision_history.delete_draft.execute(manuscript_id=manuscript_id, name=name)

    return "", 204


@draft_bp.post("/<name>/switch")
@login_required
def switch_draft(project_id: str, manuscript_id: str, name: str) -> ResponseReturnValue:
    """Switch the manuscript's current draft to the named draft."""
    container = current_app.extensions["container"]

    draft = container.revision_history.switch_draft.execute(manuscript_id=manuscript_id, name=name)

    return jsonify(_draft(draft, current=True)), 200
