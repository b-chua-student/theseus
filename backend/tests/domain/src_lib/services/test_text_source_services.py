"""Service tests for text sources, run against the in-memory repository."""

from uuid import uuid4

import pytest

from bootstrap.contexts.src_lib.module import build_source_module
from domain.src_lib.infrastructure.adapters.in_memory_source_repository import (
    InMemorySourceRepository,
)
from domain.src_lib.models.events import SourceAdded, SourceRemoved, SourceUpdated
from domain.src_lib.models.value_objects import (
    InvalidDescriptionError,
    InvalidTagsError,
    InvalidTextBodyError,
    SourceId,
)
from domain.src_lib.services.errors import SourceNotFound


class RecordingPublisher:
    def __init__(self) -> None:
        self.events: list = []

    def publish(self, events) -> None:
        self.events.extend(events)


@pytest.fixture
def repo():
    return InMemorySourceRepository()


@pytest.fixture
def publisher():
    return RecordingPublisher()


@pytest.fixture
def module(repo, publisher):
    return build_source_module(repo, publisher)


@pytest.fixture
def project_id():
    return uuid4()


def _add(module, project_id, **kw):
    kw.setdefault("title", "T")
    kw.setdefault("content", "hello world")
    return module.add_text.execute(project_id=project_id, **kw)


class TestAddTextSource:
    def test_creates_v1_text_source_and_emits_added(self, module, repo, publisher, project_id):
        sid = _add(
            module,
            project_id,
            description="d",
            tags=[" a ", "a", "", "b"],
            content_type="notes",
        )
        s = repo.get(sid)
        assert s.kind == "text" and s.version == 1 and not s.is_removed
        assert s.tags.value == ("a", "b")
        assert s.content.value == "hello world"
        assert publisher.events == [SourceAdded(sid, project_id, None, "text")]

    def test_defaults_content_type_other(self, module, repo, project_id):
        assert repo.get(_add(module, project_id)).content_type.value == "other"

    @pytest.mark.parametrize(
        ("kw", "exc"),
        [
            ({"content": ""}, InvalidTextBodyError),
            ({"content": "x" * 100_001}, InvalidTextBodyError),
            ({"description": "x" * 1001}, InvalidDescriptionError),
            ({"tags": [str(i) for i in range(11)]}, InvalidTagsError),
        ],
    )
    def test_invalid_input_persists_and_emits_nothing(
        self, module, repo, publisher, project_id, kw, exc
    ):
        with pytest.raises(exc):
            _add(module, project_id, **kw)
        assert repo.list_active() == []
        assert publisher.events == []

    def test_content_round_trips_verbatim(self, module, repo, project_id):
        body = "<script>alert(1)</script>\n  é 😀 {$ne: 1}  "
        assert repo.get(_add(module, project_id, content=body)).content.value == body


class TestUpdateTextSource:
    def test_update_bumps_version_and_emits_updated(self, module, repo, publisher, project_id):
        sid = _add(module, project_id)
        publisher.events.clear()
        module.update_text.execute(str(sid.value), title="New", content="changed", tags=["x"])
        s = repo.get(sid)
        assert (s.title.value, s.content.value, s.version) == ("New", "changed", 2)
        assert publisher.events == [SourceUpdated(sid, project_id, "text", 2)]

    def test_each_update_increments_version(self, module, repo, project_id):
        sid = _add(module, project_id)
        for _ in range(3):
            module.update_text.execute(str(sid.value), title="T", content="c")
        assert repo.get(sid).version == 4

    def test_invalid_update_changes_nothing(self, module, repo, publisher, project_id):
        sid = _add(module, project_id)
        publisher.events.clear()
        with pytest.raises(InvalidTextBodyError):
            module.update_text.execute(str(sid.value), title="New", content="")
        s = repo.get(sid)
        assert (s.title.value, s.version) == ("T", 1)
        assert publisher.events == []

    def test_unknown_removed_or_foreign_project_is_not_found(self, module, project_id):
        with pytest.raises(SourceNotFound):
            module.update_text.execute(str(uuid4()), title="T", content="c")
        sid = _add(module, project_id)
        with pytest.raises(SourceNotFound):
            module.update_text.execute(str(sid.value), "T", "c", project_id=uuid4())
        module.remove.execute(str(sid.value))
        with pytest.raises(SourceNotFound):
            module.update_text.execute(str(sid.value), title="T", content="c")

    def test_file_source_is_not_updatable_as_text(self, module, project_id):
        fid = module.add.execute("F", None, None, "ref.pdf", project_id)
        with pytest.raises(SourceNotFound):
            module.update_text.execute(str(fid.value), title="T", content="c")


class TestGetAndRemoveReuse:
    def test_get_returns_content(self, module, project_id):
        sid = _add(module, project_id, content="body")
        assert module.get.execute(str(sid.value)).content.value == "body"

    def test_remove_emits_event_and_excludes_from_list_and_search(
        self, module, repo, publisher, project_id
    ):
        sid = _add(module, project_id, content="findme")
        publisher.events.clear()
        module.remove.execute(str(sid.value))
        assert publisher.events == [SourceRemoved(sid, project_id)]
        assert repo.get(sid).removed_at is not None  # soft delete
        assert module.list_text.execute(project_id).items == []
        assert module.search_text.execute(project_id, "findme").total == 0


class TestListTextSources:
    def test_filters_sorts_and_isolates_projects(self, module, project_id):
        _add(module, project_id, title="b", tags=["t"], content_type="code")
        _add(module, project_id, title="a", content_type="notes")
        _add(module, uuid4(), title="other")
        module.add.execute("File", None, None, "f.pdf", project_id)

        by_title = module.list_text.execute(project_id, sort="title")
        assert [s.title.value for s in by_title.items] == ["a", "b"]
        assert [s.title.value for s in module.list_text.execute(project_id).items] == ["a", "b"]
        assert module.list_text.execute(project_id, content_type="code").total == 1
        assert module.list_text.execute(project_id, tag="t").items[0].title.value == "b"

    def test_paging_defaults_and_clamping(self, module, project_id):
        for i in range(25):
            _add(module, project_id, title=f"t{i:02}")
        first = module.list_text.execute(project_id)
        assert (len(first.items), first.total, first.page, first.page_size) == (20, 25, 1, 20)
        assert len(module.list_text.execute(project_id, page=2).items) == 5
        assert module.list_text.execute(project_id, page_size=1000).page_size == 100
        assert module.list_text.execute(project_id, page=0, page_size=0).page == 1

    def test_invalid_sort_or_content_type_rejected(self, module, project_id):
        with pytest.raises(ValueError):
            module.list_text.execute(project_id, sort="bogus")
        with pytest.raises(ValueError):
            module.list_text.execute(project_id, content_type="bogus")


class TestSearchTextSources:
    def test_matches_title_description_tags_content(self, module, project_id):
        _add(module, project_id, title="alpha")
        _add(module, project_id, title="x", description="beta thing")
        _add(module, project_id, title="y", tags=["gamma"])
        _add(module, project_id, title="z", content="delta text")
        for q in ("alpha", "beta", "gamma", "delta"):
            assert module.search_text.execute(project_id, q).total == 1

    def test_combines_with_filters_and_is_project_scoped(self, module, project_id):
        _add(module, project_id, title="needle", content_type="code")
        _add(module, project_id, title="needle two", content_type="notes")
        _add(module, uuid4(), title="needle foreign")
        assert module.search_text.execute(project_id, "needle").total == 2
        assert module.search_text.execute(project_id, "needle", content_type="code").total == 1

    def test_no_match_is_empty_not_error(self, module, project_id):
        _add(module, project_id)
        page = module.search_text.execute(project_id, "zzz")
        assert (page.items, page.total) == ([], 0)

    def test_query_is_treated_as_literal_text(self, module, project_id):
        _add(module, project_id, content="plain")
        assert module.search_text.execute(project_id, '{"$ne": null}').total == 0


def test_snippet_truncates_to_200_chars(module, repo, project_id):
    from domain.src_lib.services.list_text_sources import snippet_of

    sid = _add(module, project_id, content="x" * 500)
    assert len(snippet_of(repo.get(sid))) == 200


def test_source_id_type(module, project_id):
    assert isinstance(_add(module, project_id), SourceId)
