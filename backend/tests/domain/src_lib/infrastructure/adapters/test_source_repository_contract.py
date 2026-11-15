"""Contract tests shared by every SourceRepository adapter.

The Mongo variant needs a reachable MongoDB (``MONGODB_URI``, default localhost) and is
skipped otherwise. Search assertions use whole-word queries because Mongo ``$text``
matches stemmed tokens while the in-memory adapter matches substrings (design D5).
"""

import os
import time
from collections.abc import Iterator
from uuid import uuid4

import pytest
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from domain.src_lib.infrastructure.adapters.in_memory_source_repository import (
    InMemorySourceRepository,
)
from domain.src_lib.infrastructure.adapters.mongodb_source_repository import (
    SNIPPET_LENGTH,
    MongoSourceRepository,
)
from domain.src_lib.infrastructure.ports.source_repository import SourceRepository
from domain.src_lib.models.aggregates import Source
from domain.src_lib.models.value_objects import (
    Author,
    ContentType,
    Description,
    SourceTitle,
    Tags,
    TextBody,
)


@pytest.fixture(params=["memory", "mongo"])
def repo(request) -> Iterator[SourceRepository]:
    if request.param == "memory":
        yield InMemorySourceRepository()
        return

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


def make_text(repo, project_id, title="Title", content="body text", **kw) -> Source:
    source = Source.add_text(
        title=SourceTitle(title),
        content=TextBody(content),
        project_id=project_id,
        description=Description.create(kw.get("description")),
        tags=Tags.create(kw.get("tags", [])),
        content_type=kw.get("content_type", ContentType.OTHER),
    )
    repo.save(source)
    return source


def make_file(repo, project_id, title="File") -> Source:
    source = Source.add(
        title=SourceTitle(title),
        file_ref="/f.pdf",
        project_id=project_id,
        authors=[Author("A")],
        year=2020,
    )
    repo.save(source)
    return source


def ids(sources) -> set:
    return {s.id for s in sources}


def test_round_trip_preserves_text_exactly(repo):
    body = "Zażółć gęślą jaźń 🙂\n\tline2 <script>alert(1)</script> $where"
    src = make_text(repo, uuid4(), content=body, description="d", tags=["a", "b"])
    got = repo.get(src.id)
    assert got is not None
    assert got.content is not None and got.content.value == body
    assert got.kind == "text"
    assert got.version == 1
    assert list(got.tags.value) == ["a", "b"]


def test_list_excludes_full_content_but_keeps_snippet(repo):
    pid = uuid4()
    body = "x" * 5000
    make_text(repo, pid, content=body)
    items, total = repo.list_text(pid)
    assert total == 1
    assert items[0].content is not None
    assert items[0].content.value == body[:SNIPPET_LENGTH] or isinstance(
        repo, InMemorySourceRepository
    )
    assert body.startswith(items[0].content.value)


def test_list_filters_isolation_and_kind(repo):
    pid, other = uuid4(), uuid4()
    doc = make_text(repo, pid, title="Doc", content_type=ContentType.DOCUMENTATION, tags=["py"])
    make_text(repo, pid, title="Code", content_type=ContentType.CODE, tags=["js"])
    make_text(repo, other, title="Foreign")
    make_file(repo, pid)
    removed = make_text(repo, pid, title="Gone")
    removed.remove()
    repo.save(removed)

    assert repo.list_text(pid)[1] == 2
    assert ids(repo.list_text(pid, content_type=ContentType.DOCUMENTATION)[0]) == {doc.id}
    assert ids(repo.list_text(pid, tag="py")[0]) == {doc.id}
    assert repo.list_text(other)[1] == 1


def test_list_sorting_and_paging(repo):
    pid = uuid4()
    for title in ["charlie", "Alpha", "bravo"]:
        make_text(repo, pid, title=title)
        time.sleep(0.02)
    by_title, _ = repo.list_text(pid, sort="title")
    assert [s.title.value for s in by_title] == ["Alpha", "bravo", "charlie"]
    by_updated, _ = repo.list_text(pid)
    assert [s.title.value for s in by_updated] == ["bravo", "Alpha", "charlie"]

    page1, total = repo.list_text(pid, page=1, page_size=2)
    page2, _ = repo.list_text(pid, page=2, page_size=2)
    assert total == 3 and len(page1) == 2 and len(page2) == 1
    assert repo.list_text(pid, page=3, page_size=2)[0] == []


def test_search_fields_filters_and_scoping(repo):
    pid, other = uuid4(), uuid4()
    by_title = make_text(repo, pid, title="Quantum primer")
    by_desc = make_text(repo, pid, title="B", description="about quantum things")
    by_tag = make_text(repo, pid, title="C", tags=["quantum"])
    by_body = make_text(
        repo, pid, title="D", content="the quantum body", content_type=ContentType.NOTES
    )
    make_text(repo, pid, title="Unrelated", content="nothing here")
    make_text(repo, other, title="Quantum foreign")
    make_file(repo, pid, title="Quantum file")
    gone = make_text(repo, pid, title="Quantum gone")
    gone.remove()
    repo.save(gone)

    found, total = repo.search_text(pid, "quantum")
    assert total == 4
    assert ids(found) == {by_title.id, by_desc.id, by_tag.id, by_body.id}
    assert ids(repo.search_text(pid, "quantum", content_type=ContentType.NOTES)[0]) == {by_body.id}
    assert ids(repo.search_text(pid, "quantum", tag="quantum")[0]) == {by_tag.id}
    assert repo.search_text(pid, "absentword") == ([], 0)
    assert repo.search_text(pid, "quantum", page_size=2)[1] == 4


def test_search_empty_query_lists_all(repo):
    pid = uuid4()
    make_text(repo, pid, title="One")
    make_text(repo, pid, title="Two")
    items, total = repo.search_text(pid, "  ", page_size=1)
    assert total == 2 and len(items) == 1


def test_search_treats_operators_as_plain_text(repo):
    pid = uuid4()
    make_text(repo, pid, title="Plain")
    assert repo.search_text(pid, '{"$ne": null}')[1] == 0


def test_update_is_visible_everywhere_and_clears_optional_fields(repo):
    pid = uuid4()
    src = make_text(repo, pid, title="Old", content="stale", description="desc")
    src.update_text(
        title=SourceTitle("New"),
        content=TextBody("fresh"),
        description=None,
        tags=Tags.create(["t"]),
        content_type=ContentType.NOTES,
    )
    repo.save(src)

    got = repo.get(src.id)
    assert got is not None
    assert got.version == 2 and got.description is None
    assert got.title.value == "New" and got.content is not None
    assert got.content.value == "fresh"
    assert repo.list_text(pid)[1] == 1
    assert repo.search_text(pid, "stale")[1] == 0
    assert repo.search_text(pid, "fresh")[1] == 1
    assert repo.list_text(pid, tag="t")[1] == 1


def test_remove_hides_from_list_active_but_keeps_record(repo):
    src = make_text(repo, uuid4())
    src.remove()
    repo.save(src)
    assert src.id not in ids(repo.list_active())
    got = repo.get(src.id)
    assert got is not None and got.is_removed
