from uuid import UUID, uuid4

import pytest
from flask import Flask

from application.routes.manuscripts import manuscripts_bp
from services.manuscript.create_manuscript import CreateManuscriptService
from repositories.manuscript.fake_manuscript_repository import (
    FakeManuscriptRepository,
)
from repositories.revision_history.fake_revision_history_repository import (
    FakeRevisionHistoryRepository,
)


@pytest.fixture
def project_id():
    return uuid4()


@pytest.fixture
def manuscript_repository():
    return FakeManuscriptRepository()


@pytest.fixture
def revision_history_repository():
    return FakeRevisionHistoryRepository()


@pytest.fixture
def app(manuscript_repository, revision_history_repository):
    app = Flask(__name__)
    app.config["TESTING"] = True

    service = CreateManuscriptService(
        manuscript_repo=manuscript_repository,
        revision_history_repo=revision_history_repository,
    )

    app.extensions["create_manuscript_service"] = service
    app.register_blueprint(manuscripts_bp, url_prefix="/manuscripts")

    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_create_manuscript_returns_201(client, project_id):
    response = client.post(
        "/manuscripts/",
        json={
            "project_id": str(project_id),
            "title": "Research Paper",
        },
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["id"] is not None
    assert data["project_id"] == str(project_id)
    assert data["title"] == "Research Paper"


def test_create_manuscript_with_missing_title_returns_400(
    client,
    project_id,
):
    response = client.post(
        "/manuscripts/",
        json={"project_id": str(project_id)},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Title is required"


def test_create_manuscript_with_empty_title_returns_400(
    client,
    project_id,
):
    response = client.post(
        "/manuscripts/",
        json={
            "project_id": str(project_id),
            "title": "   ",
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Title is required"


def test_create_manuscript_with_missing_project_id_returns_400(client):
    response = client.post(
        "/manuscripts/",
        json={"title": "Research Paper"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Project ID is required"


def test_create_manuscript_with_invalid_project_id_returns_400(client):
    response = client.post(
        "/manuscripts/",
        json={
            "project_id": "not-a-uuid",
            "title": "Research Paper",
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid project ID"


def test_create_manuscript_with_non_json_body_returns_400(client):
    response = client.post(
        "/manuscripts/",
        data="not json",
        content_type="text/plain",
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "A JSON object is required"


def test_create_manuscript_persists_manuscript(
    client,
    manuscript_repository,
    project_id,
):
    response = client.post(
        "/manuscripts/",
        json={
            "project_id": str(project_id),
            "title": "Research Paper",
        },
    )

    assert response.status_code == 201

    manuscript_id = UUID(response.get_json()["id"])

    manuscript = manuscript_repository.get_by_id(
        manuscript_id=manuscript_id,
    )

    assert manuscript is not None
    assert manuscript.project_id == project_id
    assert manuscript.title == "Research Paper"
