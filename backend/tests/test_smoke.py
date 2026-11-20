"""Smoke tests for the application factory."""

from bootstrap.app import create_app
from domain.assistant.models.value_objects import IndexStatus, ProjectId


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
