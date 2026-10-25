from unittest.mock import MagicMock
from uuid import UUID, uuid4

from domain.manuscript.aggregates import Manuscript


def test_delete_manuscript_route(client, manuscript_repo) -> None:
    manuscript = Manuscript(id=uuid4(), project_id=uuid4(), title="My Book")
    manuscript_id = manuscript.id

    manuscript_repo.save(manuscript)

    res = client.delete(f"/api/manuscripts/{manuscript_id}")

    assert res.status_code == 204
    assert manuscript_repo.get_by_id(manuscript_id) is None


def test_invalid_request_on_delete_manuscript_route(client) -> None:
    manuscript_id = 4

    res = client.delete(f"/api/manuscripts/{manuscript_id}")

    body = res.json

    assert body["error"] == "Invalid manuscript ID format."
    assert res.status_code == 400


def test_delete_manuscript_returns_404_when_not_found(app, client) -> None:
    manuscript_id = uuid4()
    mock_service = MagicMock()
    mock_service.execute.side_effect = ValueError("Manuscript not found.")
    app.extensions["delete_manuscript_service"] = mock_service

    response = client.delete(f"/api/manuscripts/{manuscript_id}")

    assert response.status_code == 404
    mock_service.execute.assert_called_once_with(UUID(str(manuscript_id)))


def test_delete_rate_limited(limited_client) -> None:
    url = f"/api/manuscripts/{uuid4()}"
    statuses = [limited_client.delete(url).status_code for _ in range(11)]
    assert statuses[:10] == [404] * 10
    assert statuses[10] == 429
