from types import SimpleNamespace

import pytest
from flask import Flask
from flask.testing import FlaskClient

from bootstrap.contexts.manuscript.module import build_manuscript_module
from bootstrap.contexts.revision_history.module import build_revision_history_module
from bootstrap.error_handlers import register_error_handlers
from domain.manuscript.api.routes import manuscript_bp
from domain.manuscript.infrastructure.adapters.in_memory_manuscript_repository import (
    InMemoryManuscriptRepository,
)
from domain.manuscript.models.value_objects import ProjectId
from domain.revision_history.infrastructure.adapters.in_memory_revision_history_repository import (
    InMemoryRevisionHistoryRepository,
)
from domain.revision_history.infrastructure.adapters.manuscript_repository_reader import (
    ManuscriptRepositoryReader,
)
from domain.revision_history.infrastructure.adapters.manuscript_repository_writer import (
    ManuscriptRepositoryWriter,
)
from domain.src_lib.infrastructure.adapters.in_process_event_bus import InProcessEventBus

pytestmark = pytest.mark.integration


@pytest.fixture
def api_context() -> tuple[FlaskClient, str]:
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="test-secret")
    repository = InMemoryManuscriptRepository(template=False)
    publisher = InProcessEventBus()
    app.extensions["container"] = SimpleNamespace(
        manuscript=build_manuscript_module(repository, publisher),
        revision_history=build_revision_history_module(
            InMemoryRevisionHistoryRepository(),
            ManuscriptRepositoryReader(repository),
            ManuscriptRepositoryWriter(repository, publisher),
        ),
    )
    register_error_handlers(app)
    app.register_blueprint(manuscript_bp, url_prefix="/api/projects/<project_id>/manuscripts")
    return app.test_client(), f"/api/projects/{ProjectId.new().value}/manuscripts"


def test_list_requires_login(api_context: tuple[FlaskClient, str]) -> None:
    client, url = api_context
    assert client.get(url).status_code == 401


def test_manuscript_and_section_lifecycle(api_context: tuple[FlaskClient, str]) -> None:
    client, url = api_context
    with client.session_transaction() as session:
        session["user_id"] = "test-user"

    assert client.post(url, json={"title": ""}).status_code == 400
    created = client.post(url, json={"title": "Thesis"})
    assert created.status_code == 201
    manuscript_id = created.get_json()["id"]
    item_url = f"{url}/{manuscript_id}"
    assert [item["id"] for item in client.get(url).get_json()] == [manuscript_id]

    assert client.patch(f"{item_url}/title", json={"title": "Final thesis"}).status_code == 204
    assert client.post(f"{item_url}/sections", json={"heading": "Results"}).status_code == 201
    detail = client.get(item_url)
    assert detail.status_code == 200
    assert detail.get_json()["title"] == "Final thesis"
    section_id = detail.get_json()["sections"][0]["id"]

    section_url = f"{item_url}/sections/{section_id}"
    assert client.patch(f"{section_url}/heading", json={"heading": "Findings"}).status_code == 204
    assert client.put(f"{section_url}/body", json={"body": "Observed results"}).status_code == 204
    assert client.get(item_url).get_json()["sections"] == [
        {
            "id": section_id,
            "parent_id": None,
            "heading": "Findings",
            "ordinal": 1,
            "body": "Observed results",
        }
    ]

    assert client.delete(section_url).status_code == 204
    assert client.get(item_url).get_json()["sections"] == []
    assert client.delete(item_url).status_code == 204
    assert client.get(item_url).status_code == 404
