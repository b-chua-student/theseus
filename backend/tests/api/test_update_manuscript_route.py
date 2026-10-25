from uuid import uuid4

import pytest

from domain.manuscript.aggregates import Manuscript

URL = "api/manuscripts/{}"


@pytest.fixture
def existing(manuscript_repo) -> Manuscript:
    m = Manuscript(id=uuid4(), project_id=uuid4(), title="Old Title")
    manuscript_repo.save(m)
    return m


def test_update_returns_200_with_new_title(client, existing) -> None:
    resp = client.patch(URL.format(existing.id), json={"title": "New Title"})

    assert resp.status_code == 200
    assert resp.get_json()["title"] == "New Title"


def test_update_persists_change(client, manuscript_repo, existing) -> None:
    client.patch(URL.format(existing.id), json={"title": "Persisted"})

    assert manuscript_repo.get_by_id(existing.id).title == "Persisted"


def test_invalid_uuid_returns_400(client) -> None:
    resp = client.patch(URL.format("not-a-uuid"), json={"title": "X"})

    assert resp.status_code == 400
    assert resp.get_json()["error"] == "Invalid manuscript ID format."


@pytest.mark.parametrize("body", [[], "text", 123, None])
def test_non_object_json_returns_400(client, existing, body) -> None:
    resp = client.patch(URL.format(existing.id), json=body)

    assert resp.status_code == 400
    assert resp.get_json()["error"] == "Request body must be a valid JSON object."


def test_malformed_json_returns_400(client, existing) -> None:
    resp = client.patch(
        URL.format(existing.id),
        data="{bad json",
        content_type="application/json",
    )

    assert resp.status_code == 400


def test_missing_title_returns_400(client, existing) -> None:
    resp = client.patch(URL.format(existing.id), json={})

    assert resp.status_code == 400
    assert isinstance(resp.get_json()["error"], list)


def test_wrong_title_type_returns_400(client, existing) -> None:
    resp = client.patch(URL.format(existing.id), json={"title": 123})

    assert resp.status_code == 400


def test_unknown_manuscript_returns_404(client) -> None:
    resp = client.patch(URL.format(uuid4()), json={"title": "X"})

    assert resp.status_code == 404
    assert "error" in resp.get_json()


def test_rate_limit_exceeded_returns_429(limited_client, manuscript_repo) -> None:
    m = Manuscript(id=uuid4(), project_id=uuid4(), title="T")
    manuscript_repo.save(m)

    for i in range(10):
        assert limited_client.patch(URL.format(m.id), json={"title": f"T{i}"}).status_code == 200

    resp = limited_client.patch(URL.format(m.id), json={"title": "Over"})
    assert resp.status_code == 429
