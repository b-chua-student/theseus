import pytest
from uuid import UUID

def test_create_manuscript_route(client, manuscript_repo) -> None:
    book_title = "My Book"
    res = client.post("/api/manuscripts/create", json={"title": book_title})

    assert res.status_code == 201
    body = res.get_json()
    assert body["title"] == book_title

    saved = manuscript_repo.get_by_id(UUID(body["id"]))
    assert saved.title == book_title

def test_create_rate_limited(limited_client) -> None:
    statuses = [
        limited_client.post("/api/manuscripts/create", json={"title": "x"}).status_code
        for _ in range(6)
    ]
    assert statuses[:5] == [201] * 5
    assert statuses[5] == 429
