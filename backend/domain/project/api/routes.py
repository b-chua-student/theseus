from flask import Blueprint, current_app, jsonify, request, session
from flask.typing import ResponseReturnValue
from pydantic import ValidationError

from domain.identity.api.auth.routes import login_required
from .requests import (
    CreateProjectRequest,
    EditProjectDescriptionRequest,
    RenameProjectRequest,
    TransferProjectOwnershipRequest,
)
from .errors import ProjectNotFoundError


project_bp = Blueprint("project", __name__)


@project_bp.get("")
@login_required
def list_projects() -> ResponseReturnValue:
    container = current_app.extensions["container"]

    projects = container.project.list.execute(owner_id=session["user_id"])

    return jsonify([
        dict(
            id=str(p.id.value),
            name=p.name.value,
            description=p.description,
            members=[
                dict(
                    id=str(m.id.value),
                    display_name=m.display_name.value,
                    role=m.role.name.lower(),
                )
                for m in p.members
            ],
            created_at=p.created_at.isoformat(),
        )
        for p in projects
    ]), 200


@project_bp.post("")
@login_required
def create_project() -> ResponseReturnValue:
    try:
        body = CreateProjectRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as e:
        return jsonify(error="Invalid request", details=e.errors()), 400

    container = current_app.extensions["container"]

    user = container.identity.account.get_account.execute(user_id=session["user_id"])
    if user is None:
        return jsonify(error="Unauthorized"), 401

    container.project.create.execute(
        project_name=body.project_name,
        owner_id=session["user_id"],
        owner_name=user.display_name.value,
        owner_email=user.email.value,
    )

    return "", 201


@project_bp.get("/<project_id>")
@login_required
def get_project(project_id: str) -> ResponseReturnValue:
    container = current_app.extensions["container"]

    project = container.project.get.execute(project_id=project_id)

    if project is None:
        raise ProjectNotFoundError(f"Project '{project_id}' not found")

    return jsonify(
        id=str(project.id.value),
        name=project.name.value,
        description=project.description,
        owner=dict(
            id=str(project.owner.id.value),
            display_name=project.owner.display_name.value,
            email=project.owner.email.value,
        ),
        members=[
            dict(
                id=str(m.id.value),
                display_name=m.display_name.value,
                email=m.email.value,
                role=m.role.name.lower(),
            )
            for m in project.members
        ],
        created_at=project.created_at.isoformat(),
    ), 200


@project_bp.delete("/<project_id>")
@login_required
def delete_project(project_id: str) -> ResponseReturnValue:
    container = current_app.extensions["container"]

    project = container.project.get.execute(project_id=project_id)

    if project is None:
        raise ProjectNotFoundError(f"Project '{project_id}' not found")

    container.project.delete.execute(project_id=project_id)

    return "", 204


@project_bp.patch("/<project_id>/name")
@login_required
def rename_project(project_id: str) -> ResponseReturnValue:
    try:
        body = RenameProjectRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as e:
        return jsonify(error="Invalid request", details=e.errors()), 400

    container = current_app.extensions["container"]

    project = container.project.get.execute(project_id=project_id)

    if project is None:
        raise ProjectNotFoundError(f"Project '{project_id}' not found")

    container.project.rename.execute(project_id=project_id, new_name=body.name)

    return "", 204


@project_bp.put("/<project_id>/description")
@login_required
def edit_project_description(project_id: str) -> ResponseReturnValue:
    try:
        body = EditProjectDescriptionRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as e:
        return jsonify(error="Invalid request", details=e.errors()), 400

    container = current_app.extensions["container"]

    project = container.project.get.execute(project_id=project_id)

    if project is None:
        raise ProjectNotFoundError(f"Project '{project_id}' not found")

    container.project.edit_description.execute(
        project_id=project_id,
        new_description=body.description,
    )

    return "", 204


@project_bp.delete("/<project_id>/description")
@login_required
def remove_project_description(project_id: str) -> ResponseReturnValue:
    container = current_app.extensions["container"]

    project = container.project.get.execute(project_id=project_id)

    if project is None:
        raise ProjectNotFoundError(f"Project '{project_id}' not found")

    container.project.remove_description.execute(project_id=project_id)

    return "", 204


@project_bp.patch("/<project_id>/owner")
@login_required
def transfer_project_ownership(project_id: str) -> ResponseReturnValue:
    try:
        body = TransferProjectOwnershipRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as e:
        return jsonify(error="Invalid request", details=e.errors()), 400

    container = current_app.extensions["container"]

    project = container.project.get.execute(project_id=project_id)

    if project is None:
        raise ProjectNotFoundError(f"Project '{project_id}' not found")

    container.project.transfer_ownership.execute(
        project_id=project_id,
        new_owner_id=body.new_owner_id,
    )

    return "", 204
