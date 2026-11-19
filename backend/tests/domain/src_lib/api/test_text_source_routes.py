"""Integration tests for the Source Library text API."""

from types import SimpleNamespace
from uuid import uuid4

import pytest
from flask import Flask, jsonify
from flask.testing import FlaskClient

from domain.src_lib.api.errors import SourceNotFoundError
from domain.src_lib.api.routes import source_bp
from domain.src_lib.infrastructure.adapters.in_memory_source_repository import (
    InMemorySourceRepository,
)
from domain.src_lib.infrastructure.adapters.in_process_event_bus import (
    InProcessEventBus,
)
from domain.src_lib.services.add_text_source import AddTextSourceService
from domain.src_lib.services.get_source import GetSourceService
from domain.src_lib.services.list_text_sources import ListTextSourcesService
from domain.src_lib.services.remove_source import RemoveSourceService
from domain.src_lib.services.search_text_sources import SearchTextSourcesService
from domain.src_lib.services.update_text_source import UpdateTextSourceService

pytestmark = pytest.mark.integration

BASE_URL = "/api/sources/text"


@pytest.fixture
def project_id() -> str:
    return str(uuid4())


@pytest.fixture
def client(project_id: str) -> FlaskClient:
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret",
        RATELIMIT_ENABLED=False,
    )

    repository = InMemorySourceRepository()
    publisher = InProcessEventBus()
    user_id = str(uuid4())
    allowed_project: str = project_id

    project = SimpleNamespace(
        owner=SimpleNamespace(
            id=SimpleNamespace(value=user_id),
        ),
        members=[],
    )

    app.extensions["container"] = SimpleNamespace(
        source=SimpleNamespace(
            add_text=AddTextSourceService(repository, publisher),
            get=GetSourceService(repository),
            list_text=ListTextSourcesService(repository),
            search_text=SearchTextSourcesService(repository),
            update_text=UpdateTextSourceService(repository, publisher),
            remove=RemoveSourceService(repository, publisher),
        ),
        project=SimpleNamespace(
            get=SimpleNamespace(
                execute=lambda project_id: project if project_id == allowed_project else None,
            ),
        ),
    )


    @app.errorhandler(SourceNotFoundError)
    def handle_not_found(error: SourceNotFoundError):
        return jsonify(error=error.message), 404

    app.register_blueprint(
        source_bp,
        url_prefix="/api/sources",
    )

    test_client = app.test_client()

    with test_client.session_transaction() as session:
        session["user_id"] = user_id

    return test_client


def test_text_source_lifecycle(client: FlaskClient, project_id: str) -> None:
    url = f"{BASE_URL}?projectId={project_id}"

    created = client.post(
        url,
        json={
            "title": "Research Notes",
            "content": "Artificial intelligence research",
            "tags": ["research"],
            "contentType": "notes",
        },
    )

    assert created.status_code == 201
    source = created.get_json()
    assert source["version"] == 1
    assert source["kind"] == "text"

    source_id = source["id"]
    detail_url = f"{BASE_URL}/{source_id}?projectId={project_id}"

    retrieved = client.get(detail_url)
    assert retrieved.status_code == 200
    assert retrieved.get_json()["content"] == source["content"]

    listed = client.get(url)
    assert listed.status_code == 200
    assert listed.get_json()["total"] == 1
    assert listed.get_json()["items"][0]["id"] == source_id

    searched = client.get(f"{BASE_URL}/search?projectId={project_id}&q=intelligence")
    assert searched.status_code == 200
    assert searched.get_json()["total"] == 1

    updated = client.put(
        detail_url,
        json={
            "title": "Updated Notes",
            "content": "Updated research content",
        },
    )
    assert updated.status_code == 200
    assert updated.get_json()["version"] == 2
    assert updated.get_json()["title"] == "Updated Notes"

    assert client.get(detail_url).get_json()["content"] == ("Updated research content")

    deleted = client.delete(detail_url)
    assert deleted.status_code == 204

    assert client.get(detail_url).status_code == 404
    assert client.get(url).get_json()["total"] == 0


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "", "content": "Valid content"},
        {"title": "Notes", "content": ""},
        {"title": " ", "content": "Valid content"},
        {"title": "Notes", "content": " "},
        {"title": "x" * 201, "content": "Valid content"},
        {"title": "Notes", "content": "x" * 100001},
        {"title": "Notes", "content": "Valid", "contentType": "invalid"},
        {"title": "Notes", "content": "Valid", "description": "x" * 1001},
        {"title": "Notes", "content": "Valid", "tags": [str(i) for i in range(11)]},
    ],
)
def test_create_rejects_invalid_payload(
    client: FlaskClient,
    project_id: str,
    payload: dict,
) -> None:
    response = client.post(
        f"{BASE_URL}?projectId={project_id}",
        json=payload,
    )

    assert response.status_code == 400
    assert response.get_json()["errors"]


def test_requires_authentication(client: FlaskClient) -> None:
    with client.session_transaction() as session:
        session.clear()

    assert client.get(BASE_URL).status_code == 401


def test_requires_project_id(client: FlaskClient) -> None:
    assert client.get(BASE_URL).status_code == 400


def test_rejects_invalid_project_id(client: FlaskClient) -> None:
    response = client.get(f"{BASE_URL}?projectId=invalid")
    assert response.status_code == 400


def test_missing_project_returns_not_found(client: FlaskClient) -> None:
    response = client.get(f"{BASE_URL}?projectId={uuid4()}")
    assert response.status_code == 404


def test_missing_source_returns_not_found(client: FlaskClient, project_id: str) -> None:
    response = client.get(f"{BASE_URL}/{uuid4()}?projectId={project_id}")
    assert response.status_code == 404


def test_search_requires_query(client: FlaskClient, project_id: str) -> None:
    response = client.get(f"{BASE_URL}/search?projectId={project_id}")
    assert response.status_code == 400


def test_rejects_oversized_request(client: FlaskClient, project_id: str) -> None:
    response = client.post(
        f"{BASE_URL}?projectId={project_id}",
        json={"title": "Notes", "content": "x" * (513 * 1024)},
    )
    assert response.status_code == 413
