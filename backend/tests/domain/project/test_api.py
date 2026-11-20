"""HTTP route tests for the project management Flask blueprint."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest
from flask import Flask, jsonify
from flask.testing import FlaskClient
from flask.typing import ResponseReturnValue

from domain.project.api.errors import ProjectNotFoundError
from domain.project.api.routes import project_bp
from domain.project.infrastructure.adapters.in_memory_project_repository import (
    InMemoryProjectRepository,
)
from domain.project.models.entities import Member
from domain.project.models.value_objects import DisplayName, Email, MemberId, ProjectId, Role
from domain.project.services.create_project import CreateProjectService
from domain.project.services.delete_project import DeleteProjectService
from domain.project.services.edit_project_description import EditProjectDescriptionService
from domain.project.services.get_project import GetProjectService
from domain.project.services.list_projects import ListProjectsService
from domain.project.services.remove_project_description import RemoveProjectDescriptionService
from domain.project.services.rename_project import RenameProjectService
from domain.project.services.transfer_project_ownership import TransferProjectOwnershipService


@dataclass
class _FakeUser:
    """Minimal user stub returned by identity.account.get_account."""

    id: MemberId
    display_name: DisplayName
    email: Email


class _FakeGetAccountService:
    """Stub service resolving test users by ID."""

    def __init__(self, users: dict[str, _FakeUser]) -> None:
        self._users = users

    def execute(self, user_id: str) -> _FakeUser | None:
        return self._users.get(user_id)


@pytest.fixture
def api_context() -> tuple[FlaskClient, InMemoryProjectRepository, _FakeUser]:
    """Create a Flask test client wired to the project blueprint and in-memory services."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.secret_key = "test-secret"

    repo = InMemoryProjectRepository()
    user = _FakeUser(
        id=MemberId.new(),
        display_name=DisplayName("Harvey"),
        email=Email("harvey@example.com"),
    )
    users = {str(user.id.value): user}

    app.extensions["container"] = SimpleNamespace(
        identity=SimpleNamespace(
            account=SimpleNamespace(get_account=_FakeGetAccountService(users))
        ),
        project=SimpleNamespace(
            list=ListProjectsService(repo),
            create=CreateProjectService(repo),
            get=GetProjectService(repo),
            delete=DeleteProjectService(repo),
            rename=RenameProjectService(repo),
            edit_description=EditProjectDescriptionService(repo),
            remove_description=RemoveProjectDescriptionService(repo),
            transfer_ownership=TransferProjectOwnershipService(repo),
        ),
    )

    @app.errorhandler(ProjectNotFoundError)
    def handle_not_found(err: ProjectNotFoundError) -> ResponseReturnValue:
        return jsonify(error=str(err)), 404

    app.register_blueprint(project_bp, url_prefix="/api/projects")
    return app.test_client(), repo, user


def _login(client: FlaskClient, user_id: str) -> None:
    """Store user_id in the Flask test session."""
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


def test_unauthenticated_requests_are_rejected(
    api_context: tuple[FlaskClient, InMemoryProjectRepository, _FakeUser],
) -> None:
    """Verify @login_required blocks requests without an active session."""
    client, _, _ = api_context
    response = client.get("/api/projects")
    assert response.status_code == 401


def test_create_list_and_get_project_endpoints(
    api_context: tuple[FlaskClient, InMemoryProjectRepository, _FakeUser],
) -> None:
    """Verify POST /, GET /, and GET /<project_id> work end-to-end."""
    client, _, user = api_context
    _login(client, str(user.id.value))

    bad_res = client.post("/api/projects", json={"project_name": ""})
    assert bad_res.status_code == 400

    create_res = client.post("/api/projects", json={"project_name": "Theseus"})
    assert create_res.status_code == 201

    list_res = client.get("/api/projects")
    assert list_res.status_code == 200
    items = list_res.get_json()
    assert len(items) == 1
    assert items[0]["name"] == "Theseus"

    project_id = items[0]["id"]
    detail_res = client.get(f"/api/projects/{project_id}")
    assert detail_res.status_code == 200
    detail = detail_res.get_json()
    assert detail["id"] == project_id
    assert detail["owner"]["email"] == "harvey@example.com"


def test_create_project_returns_401_when_session_user_missing(
    api_context: tuple[FlaskClient, InMemoryProjectRepository, _FakeUser],
) -> None:
    """Verify POST / returns 401 if session user_id does not resolve to an account."""
    client, _, _ = api_context
    _login(client, str(MemberId.new().value))

    res = client.post("/api/projects", json={"project_name": "Orphan Project"})
    assert res.status_code == 401


def test_update_transfer_and_delete_project_endpoints(
    api_context: tuple[FlaskClient, InMemoryProjectRepository, _FakeUser],
) -> None:
    """Verify PATCH name, PUT/DELETE description, PATCH owner, and DELETE project routes."""
    client, repo, user = api_context
    _login(client, str(user.id.value))

    client.post("/api/projects", json={"project_name": "Initial"})
    project_id = client.get("/api/projects").get_json()[0]["id"]

    assert client.patch(f"/api/projects/{project_id}/name", json={"name": ""}).status_code == 400
    assert (
        client.patch(f"/api/projects/{project_id}/name", json={"name": "Renamed"}).status_code
        == 204
    )

    assert (
        client.put(f"/api/projects/{project_id}/description", json={"description": ""}).status_code
        == 400
    )
    assert (
        client.put(
            f"/api/projects/{project_id}/description",
            json={"description": "New description"},
        ).status_code
        == 204
    )
    assert client.get(f"/api/projects/{project_id}").get_json()["description"] == "New description"

    assert client.delete(f"/api/projects/{project_id}/description").status_code == 204
    assert client.get(f"/api/projects/{project_id}").get_json()["description"] is None

    # Add a member directly to test ownership transfer endpoint
    stored = repo.get_project_by_id(ProjectId.from_str(project_id))
    assert stored is not None
    new_owner = Member.join(DisplayName("Nick"), Email("nick@example.com"), Role.EDITOR)
    stored.add_member(new_owner)
    repo.update_project(stored)

    assert (
        client.patch(f"/api/projects/{project_id}/owner", json={"new_owner_id": ""}).status_code
        == 400
    )
    assert (
        client.patch(
            f"/api/projects/{project_id}/owner",
            json={"new_owner_id": str(new_owner.id.value)},
        ).status_code
        == 204
    )
    assert (
        client.get(f"/api/projects/{project_id}").get_json()["owner"]["email"] == "nick@example.com"
    )

    assert client.delete(f"/api/projects/{project_id}").status_code == 204
    assert client.get(f"/api/projects/{project_id}").status_code == 404


def test_missing_project_returns_404_across_item_endpoints(
    api_context: tuple[FlaskClient, InMemoryProjectRepository, _FakeUser],
) -> None:
    """Verify all /<project_id> endpoints raise ProjectNotFoundError (404) for unknown IDs."""
    client, _, user = api_context
    _login(client, str(user.id.value))
    missing = str(ProjectId.new().value)

    assert client.get(f"/api/projects/{missing}").status_code == 404
    assert client.delete(f"/api/projects/{missing}").status_code == 404
    assert client.patch(f"/api/projects/{missing}/name", json={"name": "Valid"}).status_code == 404
    assert (
        client.put(
            f"/api/projects/{missing}/description", json={"description": "Valid"}
        ).status_code
        == 404
    )
    assert client.delete(f"/api/projects/{missing}/description").status_code == 404
    assert (
        client.patch(
            f"/api/projects/{missing}/owner",
            json={"new_owner_id": str(MemberId.new().value)},
        ).status_code
        == 404
    )
