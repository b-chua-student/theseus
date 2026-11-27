"""Smoke tests for the application factory."""

import pytest

from bootstrap.app import create_app
from domain.assistant.models.value_objects import DocumentRefId, IndexStatus, ProjectId

pytestmark = pytest.mark.integration


def test_contexts_share_dependencies() -> None:
    """Exercise context wiring through HTTP and verify source indexing."""
    app = create_app({"TESTING": True})

    with app.test_client() as client:
        registration = client.post(
            "/api/auth/register",
            json={
                "display_name": "Example Writer",
                "email": "writer@example.com",
                "password": "Example-password-42",
            },
        )
        assert registration.status_code == 201
        assert client.post("/api/projects", json={"project_name": "Research"}).status_code == 201
        project_id = client.get("/api/projects").get_json()[0]["id"]
        manuscripts = f"/api/projects/{project_id}/manuscripts"

        manuscript = client.post(manuscripts, json={"title": "First draft", "template": False})
        assert manuscript.status_code == 201
        manuscript_url = f"{manuscripts}/{manuscript.get_json()['id']}"
        assert client.post(f"{manuscript_url}/revisions/history").status_code == 201
        assert client.get(f"{manuscript_url}/drafts").status_code == 200
        assert client.get(f"{manuscript_url}/indexing-status").get_json()["status"] == "not_indexed"
        assert client.post(f"/api/projects/{project_id}/conversations").status_code == 503

        source = client.post(
            f"/api/sources/text?projectId={project_id}",
            json={"title": "Research notes", "content": "Notes for the first draft."},
        )
        assert source.status_code == 201

    repository = app.extensions["container"].assistant.indexed_document_repository
    documents = repository.list_by_project(ProjectId.from_str(project_id))
    assert [document.status for document in documents] == [IndexStatus.INDEXED]


def test_health() -> None:
    """Verify the health endpoint responds successfully over HTTP."""
    app = create_app({"TESTING": True})

    with app.test_client() as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == {"status": "ok"}


def test_restoring_a_revision_replaces_indexed_manuscript_content() -> None:
    app = create_app({"TESTING": True})

    with app.test_client() as client:
        assert (
            client.post(
                "/api/auth/register",
                json={
                    "display_name": "Example Writer",
                    "email": "restore@example.com",
                    "password": "Example-password-42",
                },
            ).status_code
            == 201
        )
        assert client.post("/api/projects", json={"project_name": "Research"}).status_code == 201
        project_id = client.get("/api/projects").get_json()[0]["id"]
        manuscripts = f"/api/projects/{project_id}/manuscripts"
        created = client.post(manuscripts, json={"title": "First draft"})
        assert created.status_code == 201
        manuscript_id = created.get_json()["id"]
        url = f"{manuscripts}/{manuscript_id}"
        assert client.post(f"{url}/sections", json={"heading": "Results"}).status_code == 201
        section_id = client.get(url).get_json()["sections"][0]["id"]
        body_url = f"{url}/sections/{section_id}/body"
        revisions = f"{url}/revisions"

        assert client.put(body_url, json={"body": "Original findings"}).status_code == 204
        assert client.post(f"{revisions}/history").status_code == 201
        initial = client.get(revisions).get_json()[0]["id"]

        assert client.put(body_url, json={"body": "Updated findings"}).status_code == 204
        assert client.post(revisions, json={"message": "Update findings"}).status_code == 201

        repository = app.extensions["container"].assistant.indexed_document_repository
        ref = DocumentRefId.from_str(manuscript_id)
        updated = repository.get_by_doc_ref_id(ref)
        assert updated is not None
        assert updated.status == IndexStatus.INDEXED
        assert any("Updated findings" in chunk.text for chunk in updated.chunks)

        assert client.post(f"{revisions}/{initial}/restore", json={}).status_code == 200

        restored = repository.get_by_doc_ref_id(ref)
        assert restored is not None
        assert restored.status == IndexStatus.INDEXED
        assert any("Original findings" in chunk.text for chunk in restored.chunks)
        assert all("Updated findings" not in chunk.text for chunk in restored.chunks)
