from types import SimpleNamespace

import pytest
from flask import Flask
from flask.testing import FlaskClient

from bootstrap.contexts.manuscript.module import build_manuscript_module
from bootstrap.contexts.revision_history.module import RevisionHistoryModule
from bootstrap.error_handlers import register_error_handlers
from domain.manuscript.api.routes import manuscript_bp
from domain.manuscript.infrastructure.adapters.in_memory_manuscript_repository import (
    InMemoryManuscriptRepository,
)
from domain.manuscript.models.aggregates import Manuscript
from domain.manuscript.models.value_objects import Heading, ManuscriptTitle, ProjectId
from domain.revision_history.api.routes import draft_bp, revision_bp
from domain.src_lib.infrastructure.adapters.in_process_event_bus import InProcessEventBus

pytestmark = pytest.mark.integration


@pytest.fixture
def api_context(
    history_services: RevisionHistoryModule,
    manuscript_repository: InMemoryManuscriptRepository,
    publisher: InProcessEventBus,
) -> tuple[FlaskClient, str, str]:
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="test-secret")
    manuscript = Manuscript.create(ProjectId.new(), ManuscriptTitle("Thesis"), template=False)
    manuscript.append_section(None, Heading("Results"))
    manuscript_repository.save(manuscript)
    app.extensions["container"] = SimpleNamespace(
        manuscript=build_manuscript_module(manuscript_repository, publisher),
        revision_history=history_services,
    )
    register_error_handlers(app)
    prefix = "/api/projects/<project_id>/manuscripts"
    app.register_blueprint(manuscript_bp, url_prefix=prefix)
    app.register_blueprint(revision_bp, url_prefix=f"{prefix}/<manuscript_id>/revisions")
    app.register_blueprint(draft_bp, url_prefix=f"{prefix}/<manuscript_id>/drafts")
    url = f"/api/projects/{manuscript.project_id.value}/manuscripts/{manuscript.id.value}"
    return app.test_client(), url, str(manuscript.sections[0].id.value)


def test_revision_and_draft_lists_require_login(api_context: tuple[FlaskClient, str, str]) -> None:
    client, url, _ = api_context
    assert client.get(f"{url}/revisions").status_code == 401
    assert client.get(f"{url}/drafts").status_code == 401


def test_commit_and_restore_update_the_committed_manuscript_view(
    api_context: tuple[FlaskClient, str, str],
) -> None:
    client, url, section_id = api_context
    with client.session_transaction() as session:
        session["user_id"] = "test-user"

    revisions = f"{url}/revisions"
    assert client.get(revisions).status_code == 404
    assert client.post(f"{revisions}/history").status_code == 201
    first = client.get(revisions).get_json()[0]
    assert client.post(revisions, json={"message": ""}).status_code == 400
    unchanged = client.post(revisions, json={"message": "No changes"})
    assert unchanged.status_code == 409
    assert unchanged.get_json()["code"] == "revision.no_changes"

    assert (
        client.put(f"{url}/sections/{section_id}/body", json={"body": "Findings"}).status_code
        == 204
    )
    assert client.get(f"{url}?view=working").get_json()["sections"][0]["body"] == "Findings"
    assert client.get(url).get_json()["sections"][0]["body"] == ""

    committed = client.post(revisions, json={"message": "Record findings"})
    assert committed.status_code == 201
    committed_id = committed.get_json()["id"]
    assert client.get(f"{revisions}/{committed_id}").get_json()["sections"][0]["body"] == "Findings"
    assert client.get(url).get_json()["sections"][0]["body"] == "Findings"

    restored = client.post(f"{revisions}/{first['id']}/restore", json={})
    assert restored.status_code == 200
    restored_id = restored.get_json()["id"]
    assert [entry["id"] for entry in client.get(revisions).get_json()] == [
        restored_id,
        committed_id,
        first["id"],
    ]
    assert client.get(f"{url}?view=working").get_json()["sections"][0]["body"] == ""


def test_draft_lifecycle(api_context: tuple[FlaskClient, str, str]) -> None:
    client, url, _ = api_context
    with client.session_transaction() as session:
        session["user_id"] = "test-user"

    assert client.post(f"{url}/revisions/history").status_code == 201
    drafts = f"{url}/drafts"
    created = client.post(drafts, json={"name": "experiment"})
    assert created.status_code == 201
    assert created.get_json()["is_current"] is False
    assert client.post(f"{drafts}/experiment/switch").get_json()["is_current"] is True
    renamed = client.patch(f"{drafts}/experiment", json={"name": "review"})
    assert renamed.status_code == 200
    assert renamed.get_json()["is_current"] is True
    assert client.get(f"{drafts}/experiment").status_code == 404
    assert client.delete(f"{drafts}/review").status_code == 400
    assert client.post(f"{drafts}/main/switch").status_code == 200
    assert client.delete(f"{drafts}/review").status_code == 204
    assert [draft["name"] for draft in client.get(drafts).get_json()] == ["main"]


def test_merge_conflict_and_invalid_resolution_leave_current_content_intact(
    api_context: tuple[FlaskClient, str, str],
) -> None:
    client, url, section_id = api_context
    with client.session_transaction() as session:
        session["user_id"] = "test-user"

    revisions = f"{url}/revisions"
    drafts = f"{url}/drafts"
    body_url = f"{url}/sections/{section_id}/body"
    assert client.post(f"{revisions}/history").status_code == 201
    assert client.post(drafts, json={"name": "review"}).status_code == 201
    assert client.post(f"{drafts}/review/switch").status_code == 200
    assert client.put(body_url, json={"body": "Reviewed findings"}).status_code == 204
    assert client.post(revisions, json={"message": "Review findings"}).status_code == 201
    assert client.post(f"{drafts}/main/switch").status_code == 200
    assert client.put(body_url, json={"body": "Original findings"}).status_code == 204
    assert client.post(revisions, json={"message": "Record findings"}).status_code == 201
    before = client.get(revisions).get_json()

    merge_url = f"{drafts}/review/merge"
    conflict = client.post(merge_url, json={})
    assert conflict.status_code == 409
    assert conflict.get_json()["code"] == "revision.merge_conflict"
    assert [(item["section_id"], item["field"]) for item in conflict.get_json()["conflicts"]] == [
        (section_id, "body")
    ]

    resolution = {"section_id": section_id, "field": "heading", "choice": "source"}
    invalid = client.post(merge_url, json={"resolutions": [resolution]})
    assert invalid.status_code == 422
    assert invalid.get_json()["code"] == "revision.invalid_resolution"
    assert client.get(revisions).get_json() == before
    assert (
        client.get(f"{url}?view=working").get_json()["sections"][0]["body"] == "Original findings"
    )

    resolution["field"] = "body"
    assert client.post(merge_url, json={"resolutions": [resolution]}).status_code == 200
    assert client.get(url).get_json()["sections"][0]["body"] == "Reviewed findings"
