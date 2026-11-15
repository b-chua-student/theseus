"""Mongo-backed integration and performance checks for text sources (N1, N2, N3, N5).

The real Flask routes and services run against ``MongoSourceRepository``; every other
repository stays in memory. The module is skipped when MongoDB is unreachable
(``MONGODB_URI``, default localhost), like the repository contract tests.
"""

import os
import time
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from bootstrap.app import create_app
from bootstrap.container import build_container
from domain.src_lib.infrastructure.adapters.mongodb_source_repository import (
    MongoSourceRepository,
)

BASE = "/api/sources/text"
UPLOAD_LIMIT_SECONDS = 2.0  # N1
SEARCH_LIMIT_SECONDS = 1.0  # N2
SEARCH_CORPUS = 1000
CONCURRENT_USERS = 20


@pytest.fixture
def mongo_repo() -> Iterator[MongoSourceRepository]:
    client: MongoClient = MongoClient(
        os.environ.get("MONGODB_URI", "mongodb://localhost:27017"),
        serverSelectionTimeoutMS=500,
        tz_aware=True,
    )
    try:
        client.admin.command("ping")
    except PyMongoError:
        pytest.skip("MongoDB not reachable")
    database = client[os.environ.get("MONGODB_DB", "theseus_contract_test")]
    name = f"sources_{uuid4().hex}"
    try:
        yield MongoSourceRepository(database, collection=name)
    finally:
        database.drop_collection(name)
        client.close()


@pytest.fixture
def app(mongo_repo):
    return create_app(
        config={"TESTING": True, "SECRET_KEY": "test-secret", "RATELIMIT_ENABLED": False},
        container=build_container(source_repo=mongo_repo),
    )


def signed_in(app, email):
    client = app.test_client()
    res = client.post(
        "/api/auth/register",
        json={"display_name": "Tester", "email": email, "password": "correct-horse-battery"},
    )
    assert res.status_code == 201
    client.post("/api/projects", json={"project_name": "P"})
    return client, client.get("/api/projects").get_json()[0]["id"]


def url(pid, path="", **params):
    qs = "&".join([f"projectId={pid}"] + [f"{k}={v}" for k, v in params.items()])
    return f"{BASE}{path}?{qs}"


@pytest.fixture
def user(app):
    return signed_in(app, "a@example.com")


def test_crud_and_search_round_trip_on_mongo(user):
    client, pid = user
    created = client.post(
        url(pid),
        json={"title": "Quantum primer", "content": "entanglement basics", "tags": ["physics"]},
    )
    assert created.status_code == 201
    sid = created.get_json()["id"]

    listed = client.get(url(pid)).get_json()
    assert listed["total"] == 1 and "content" not in listed["items"][0]
    assert client.get(url(pid, "/search", q="entanglement")).get_json()["total"] == 1

    updated = client.put(url(pid, f"/{sid}"), json={"title": "Quantum primer", "content": "fresh"})
    assert updated.status_code == 200 and updated.get_json()["version"] == 2
    assert client.get(url(pid, "/search", q="entanglement")).get_json()["total"] == 0
    assert client.get(url(pid, "/search", q="fresh")).get_json()["total"] == 1

    assert client.delete(url(pid, f"/{sid}")).status_code == 204
    assert client.get(url(pid, f"/{sid}")).status_code == 404
    assert client.get(url(pid)).get_json()["total"] == 0
    assert client.get(url(pid, "/search", q="fresh")).get_json()["total"] == 0


@pytest.mark.performance
def test_n1_create_10kb_under_2_seconds(user):
    client, pid = user
    body = "a" * 10_000
    started = time.perf_counter()
    res = client.post(url(pid), json={"title": "Ten KB", "content": body})
    elapsed = time.perf_counter() - started
    assert res.status_code == 201
    assert elapsed < UPLOAD_LIMIT_SECONDS, f"create took {elapsed:.2f}s"


@pytest.mark.performance
def test_n2_search_over_1000_documents_under_1_second(user, mongo_repo):
    client, pid = user
    from uuid import UUID

    from domain.src_lib.models.aggregates import Source
    from domain.src_lib.models.value_objects import SourceTitle, TextBody

    for i in range(SEARCH_CORPUS):
        word = "needleword" if i % 100 == 0 else "filler"
        mongo_repo.save(
            Source.add_text(
                title=SourceTitle(f"Doc {i}"),
                content=TextBody(f"{word} paragraph number {i} " * 40),
                project_id=UUID(pid),
            )
        )
    client.get(url(pid, "/search", q="needleword"))  # warm the connection and index
    started = time.perf_counter()
    res = client.get(url(pid, "/search", q="needleword"))
    elapsed = time.perf_counter() - started
    assert res.status_code == 200 and res.get_json()["total"] == SEARCH_CORPUS // 100
    assert elapsed < SEARCH_LIMIT_SECONDS, f"search took {elapsed:.2f}s"


@pytest.mark.performance
@pytest.mark.concurrency
def test_n3_concurrent_users_are_isolated(app):
    users = [signed_in(app, f"user{i}@example.com") for i in range(CONCURRENT_USERS)]

    def work(i: int) -> tuple[int, int, set[str], set[str]]:
        client, pid = users[i]
        res = client.post(url(pid), json={"title": f"Mine {i}", "content": f"secret-{i} body"})
        listed = client.get(url(pid)).get_json()
        found = client.get(url(pid, "/search", q=f"secret-{i}")).get_json()
        return (
            res.status_code,
            listed["total"],
            {item["title"] for item in listed["items"]},
            {item["title"] for item in found["items"]},
        )

    with ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as pool:
        results = list(pool.map(work, range(CONCURRENT_USERS)))

    for i, (status, total, titles, found) in enumerate(results):
        assert status == 201
        assert total == 1 and titles == {f"Mine {i}"}
        assert found <= {f"Mine {i}"}


@pytest.mark.storage
def test_n5_100k_characters_round_trip_byte_for_byte(user):
    client, pid = user
    unit = "Zażółć gęślą jaźń 🙂 <b>&amp;</b> $where\r\n\t"
    body = (unit * (100_000 // len(unit) + 1))[:100_000]
    assert len(body) == 100_000
    created = client.post(url(pid), json={"title": "Big", "content": body})
    assert created.status_code == 201
    fetched = client.get(url(pid, f"/{created.get_json()['id']}")).get_json()
    assert fetched["content"].encode("utf-8") == body.encode("utf-8")
