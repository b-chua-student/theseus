import pytest
from uuid import UUID, uuid4

def test_delete_manuscript_route(client, manuscript_repo) -> None:
    book_title = "My Book"
    res = client.post("/api/manuscripts/create", json={"title": book_title})
    body = res.get_json()
    manuscript_id = UUID(body["id"])

    res = client.delete(f"/api/manuscripts/{manuscript_id}")

    assert res.status_code == 204
    assert manuscript_repo.get_by_id(manuscript_id) is None

def test_delete_rate_limited(limited_client) -> None:
    url = f"/api/manuscripts/{uuid4()}"
    statuses = [limited_client.delete(url).status_code for _ in range(11)]
    assert statuses[:10] == [404] * 10
    assert statuses[10] == 429
