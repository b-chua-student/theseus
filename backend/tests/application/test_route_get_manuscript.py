import pytest
from uuid import UUID, uuid4

def test_get_manuscript_route(client, manuscript_repo) -> None:
    book_title = "My Book"
    res = client.post("/api/manuscripts/create", json={"title": book_title})
    body = res.get_json()
    manuscript_id = UUID(body["id"])

    res = client.get(f"/api/manuscripts/{manuscript_id}")

    assert res.status_code == 200
    assert body["title"] == book_title

def test_get_rate_limited(limited_client) -> None:
    url = f"/api/manuscripts/{uuid4()}"
    statuses = [limited_client.get(url).status_code for _ in range(21)]
    assert statuses[:20] == [404] * 20
    assert statuses[20] == 429
