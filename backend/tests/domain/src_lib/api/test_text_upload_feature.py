"""API-level scenarios of ``source_library_text_upload.feature`` on in-memory adapters.

Each test is named after a feature scenario. Scenarios tagged @ui, @performance,
@concurrency, @storage, @accessibility and @responsive are out of scope here.
Scenarios already covered one-to-one by ``test_text_source_routes.py`` (auth matrix,
boundaries, 429, cross-project 404) are only re-checked where the feature asserts
something extra, such as exact error messages.
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pytest

from bootstrap.app import create_app
from bootstrap.container import build_container
from domain.assistant.infrastructure.ports.chat_model import ChatModel
from domain.assistant.models.value_objects import Answer

BASE = "/api/sources/text"


def _register(app, email):
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


def create(client, pid, **overrides):
    body = {"title": "Title", "content": "Hello world"} | overrides
    return client.post(url(pid), json=body)


def messages(res):
    return {e["field"]: e["message"] for e in res.get_json()["errors"]}


@pytest.fixture
def me(app):
    return _register(app, "me@example.com")


@pytest.fixture
def client(me):
    return me[0]


@pytest.fixture
def pid(me):
    return me[1]


@pytest.fixture
def other(app):
    return _register(app, "other@example.com")


# --------------------------------------------------------------------------- Create


class TestCreate:
    def test_upload_text_with_required_fields_only(self, client, pid):
        res = create(
            client, pid, title="API Spec v1", content="GET /users returns a list of users."
        )
        assert res.status_code == 201
        body = res.get_json()
        assert body["version"] == 1
        assert body["contentType"] == "other"
        assert body.get("removed", False) is False
        assert body.get("isRemoved", False) is False

    def test_upload_text_with_all_metadata(self, client, pid):
        res = create(
            client,
            pid,
            title="Sprint Planning Notes",
            description="Notes from sprint 12 planning",
            tags=["sprint", "planning", "q3"],
            contentType="notes",
            content="Decided to prioritize search performance.",
        )
        body = res.get_json()
        assert res.status_code == 201
        assert body["tags"] == ["sprint", "planning", "q3"]
        assert body["contentType"] == "notes"

    def test_reject_empty_content(self, client, pid):
        res = create(client, pid, title="Empty Doc", content="")
        assert res.status_code == 400
        assert messages(res)["content"] == "Content is required"
        assert client.get(url(pid)).get_json()["total"] == 0

    def test_reject_missing_title(self, client, pid):
        res = create(client, pid, title="", content="Some content")
        assert res.status_code == 400
        assert messages(res)["title"] == "Title is required"
        assert client.get(url(pid)).get_json()["total"] == 0

    def test_content_length_over_limit_message(self, client, pid):
        res = create(client, pid, content="x" * 100_001)
        assert res.status_code == 400
        assert "100,000" in messages(res)["content"]

    @pytest.mark.parametrize(
        "field,length,expected",
        [
            ("title", 200, None),
            ("title", 201, "200"),
            ("description", 1000, None),
            ("description", 1001, "1000"),
        ],
    )
    def test_metadata_limits(self, client, pid, field, length, expected):
        res = create(client, pid, **{field: "a" * length})
        if expected is None:
            assert res.status_code == 201
        else:
            assert res.status_code == 400
            assert expected in messages(res)[field]

    @pytest.mark.parametrize("count,expected", [(10, None), (11, "10 tags")])
    def test_tag_limit(self, client, pid, count, expected):
        res = create(client, pid, tags=[f"t{i}" for i in range(count)])
        if expected is None:
            assert res.status_code == 201
        else:
            assert res.status_code == 400
            assert expected in messages(res)["tags"]

    def test_reject_invalid_content_type_lists_allowed_values(self, client, pid):
        res = create(client, pid, contentType="spreadsheet")
        assert res.status_code == 400
        message = messages(res)["contentType"]
        for allowed in ("documentation", "notes", "code", "other"):
            assert allowed in message

    def test_preserve_utf8_characters(self, client, pid):
        text = "Héllo 世界 🌏 مرحبا"
        sid = create(client, pid, content=text).get_json()["id"]
        res = client.get(url(pid, f"/{sid}"))
        assert res.get_json()["content"] == text


# --------------------------------------------------------------------------- Read


class TestRead:
    def test_view_a_specific_item(self, client, pid):
        sid = create(
            client,
            pid,
            title="API Spec v1",
            description="d",
            tags=["api"],
            contentType="documentation",
        ).get_json()["id"]
        body = client.get(url(pid, f"/{sid}")).get_json()
        for key in (
            "title",
            "description",
            "tags",
            "contentType",
            "content",
            "createdAt",
            "updatedAt",
        ):
            assert key in body, key
        assert body["title"] == "API Spec v1"

    def test_list_with_pagination(self, client, pid):
        for i in range(25):
            create(client, pid, title=f"Doc {i:02d}")
        first = client.get(url(pid)).get_json()
        assert (first["total"], len(first["items"]), first["page"], first["pageSize"]) == (
            25,
            20,
            1,
            20,
        )
        second = client.get(url(pid, page=2)).get_json()
        assert len(second["items"]) == 5
        ids = {i["id"] for i in first["items"]} | {i["id"] for i in second["items"]}
        assert len(ids) == 25

    @pytest.mark.parametrize(
        "param,value,expected",
        [("contentType", "code", {"c1"}), ("tag", "api", {"c1", "n1"})],
    )
    def test_filter_the_list(self, client, pid, param, value, expected):
        create(client, pid, title="c1", contentType="code", tags=["api"])
        create(client, pid, title="n1", contentType="notes", tags=["api"])
        create(client, pid, title="n2", contentType="notes", tags=["other"])
        items = client.get(url(pid, **{param: value})).get_json()["items"]
        assert {i["title"] for i in items} == expected

    def test_sort_by_title_and_by_date(self, client, pid):
        for title in ("b", "C", "a"):
            create(client, pid, title=title)
        by_title = [i["title"] for i in client.get(url(pid, sort="title")).get_json()["items"]]
        assert by_title == ["a", "b", "C"]
        by_date = client.get(url(pid, sort="updatedAt")).get_json()["items"]
        stamps = [datetime.fromisoformat(i["updatedAt"].replace("Z", "+00:00")) for i in by_date]
        assert stamps == sorted(stamps, reverse=True)

    def test_cannot_view_another_users_content(self, client, pid, other):
        other_client, other_pid = other
        sid = create(other_client, other_pid).get_json()["id"]
        assert client.get(url(pid, f"/{sid}")).status_code in (403, 404)
        assert client.get(url(other_pid, f"/{sid}")).status_code in (403, 404)

    def test_request_non_existent_item(self, client, pid):
        assert client.get(url(pid, f"/{uuid4()}")).status_code == 404


# --------------------------------------------------------------------------- Update


class TestUpdate:
    def test_edit_content_increments_version(self, client, pid):
        created = create(client, pid).get_json()
        res = client.put(
            url(pid, f"/{created['id']}"),
            json={"title": created["title"], "content": "changed"},
        )
        body = res.get_json()
        assert res.status_code == 200
        assert body["content"] == "changed"
        assert body["version"] == 2
        parse = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))  # noqa: E731
        assert parse(body["updatedAt"]) > parse(body["createdAt"])

    def test_edit_metadata_only_keeps_content(self, client, pid):
        created = create(client, pid, tags=["a"], content="original").get_json()
        res = client.put(
            url(pid, f"/{created['id']}"),
            json={"title": created["title"], "content": "original", "tags": ["b", "c"]},
        )
        body = res.get_json()
        assert body["tags"] == ["b", "c"]
        assert body["content"] == "original"

    def test_update_follows_create_validation(self, client, pid):
        sid = create(client, pid).get_json()["id"]
        res = client.put(url(pid, f"/{sid}"), json={"title": "", "content": "x"})
        assert res.status_code == 400
        assert messages(res)["title"] == "Title is required"
        stored = client.get(url(pid, f"/{sid}")).get_json()
        assert (stored["title"], stored["content"], stored["version"]) == (
            "Title",
            "Hello world",
            1,
        )

    def test_cannot_update_another_users_content(self, client, pid, other):
        other_client, other_pid = other
        sid = create(other_client, other_pid).get_json()["id"]
        for target in (pid, other_pid):
            res = client.put(url(target, f"/{sid}"), json={"title": "hacked", "content": "x"})
            assert res.status_code in (403, 404)
        stored = other_client.get(url(other_pid, f"/{sid}")).get_json()
        assert (stored["title"], stored["version"]) == ("Title", 1)


# --------------------------------------------------------------------------- Delete


class TestDelete:
    def test_soft_delete(self, app, client, pid):
        sid = create(client, pid, title="Old Notes", content="stale zebra").get_json()["id"]
        assert client.delete(url(pid, f"/{sid}")).status_code == 204
        assert client.get(url(pid)).get_json()["items"] == []
        assert client.get(url(pid, "/search", q="zebra")).get_json()["items"] == []
        stored = app.extensions["container"].source.get.execute(source_id=sid)
        assert stored is not None and stored.is_removed

    def test_active_until_deleted(self, client, pid):
        # "Cancel deletion" is a client-side action: with no request sent, nothing changes.
        sid = create(client, pid, title="Old Notes").get_json()["id"]
        assert client.get(url(pid, f"/{sid}")).status_code == 200
        assert [i["id"] for i in client.get(url(pid)).get_json()["items"]] == [sid]

    def test_cannot_delete_another_users_content(self, client, pid, other):
        other_client, other_pid = other
        sid = create(other_client, other_pid).get_json()["id"]
        for target in (pid, other_pid):
            assert client.delete(url(target, f"/{sid}")).status_code in (403, 404)
        assert other_client.get(url(other_pid, f"/{sid}")).status_code == 200


# --------------------------------------------------------------------------- Search


class TestSearch:
    def test_search_by_keyword_in_content(self, client, pid):
        create(client, pid, title="Limits", content="We apply rate limiting per user.")
        items = client.get(url(pid, "/search", q="rate%20limiting")).get_json()["items"]
        assert [i["title"] for i in items] == ["Limits"]

    @pytest.mark.parametrize(
        "field,text",
        [("title", "onboarding"), ("description", "quarterly"), ("tags", "architecture")],
    )
    def test_search_matches_multiple_fields(self, client, pid, field, text):
        value = [text] if field == "tags" else text
        sid = create(client, pid, **{field: value}, content="unrelated body").get_json()["id"]
        items = client.get(url(pid, "/search", q=text)).get_json()["items"]
        assert [i["id"] for i in items] == [sid]

    def test_search_with_no_matches(self, client, pid):
        res = client.get(url(pid, "/search", q="zzzz-no-match"))
        assert res.status_code == 200
        assert res.get_json()["items"] == []

    def test_search_combined_with_filters(self, client, pid):
        create(client, pid, title="n", content="auth flow", contentType="notes")
        create(client, pid, title="c", content="auth flow", contentType="code")
        items = client.get(url(pid, "/search", q="auth", contentType="code")).get_json()["items"]
        assert [i["title"] for i in items] == ["c"]

    def test_search_only_returns_my_content(self, client, pid, other):
        other_client, other_pid = other
        create(other_client, other_pid, content="confidential plans")
        assert client.get(url(pid, "/search", q="confidential")).get_json()["items"] == []
        # also not reachable by pointing at the other user's project
        assert client.get(url(other_pid, "/search", q="confidential")).status_code == 404


# --------------------------------------------------------------------------- Integration


class TestIntegration:
    def test_uploaded_text_appears_in_source_library(self, client, pid):
        sid = create(client, pid, title="API Spec v1").get_json()["id"]
        res = client.get(f"/api/sources?projectId={pid}")
        assert res.status_code == 200
        listed = res.get_json()
        listed = listed.get("items", listed) if isinstance(listed, dict) else listed
        assert sid in {s["id"] for s in listed}


class _RecordingModel(ChatModel):
    def __init__(self) -> None:
        self.context: list | None = None

    def reply(self, history, query, context=None):  # noqa: ANN001
        self.context = context
        return Answer("ok")


@pytest.fixture
def grounded():
    model = _RecordingModel()
    app = create_app(
        config={"TESTING": True, "SECRET_KEY": "test-secret", "RATELIMIT_ENABLED": False},
        container=build_container(chat_model=model),
    )
    client, pid = _register(app, "g@example.com")
    return client, pid, model


def _ask(client, pid, query):
    cid = client.post(f"/api/projects/{pid}/conversations").get_json()["id"]
    res = client.post(f"/api/projects/{pid}/conversations/{cid}/exchanges", json={"query": query})
    assert res.status_code == 201
    return res


class TestGrounding:
    ENDPOINT_TEXT = "GET /users returns a list of users."

    def test_uploaded_text_is_used_for_grounding(self, grounded):
        client, pid, model = grounded
        create(client, pid, title="Users", content=self.ENDPOINT_TEXT)
        _ask(client, pid, self.ENDPOINT_TEXT)
        assert model.context
        assert any(self.ENDPOINT_TEXT in c.text for c in model.context)

    def test_edited_text_replaces_old_grounding(self, grounded):
        client, pid, model = grounded
        sid = create(client, pid, title="Users", content=self.ENDPOINT_TEXT).get_json()["id"]
        client.put(url(pid, f"/{sid}"), json={"title": "Users", "content": "POST /orders creates."})
        _ask(client, pid, "POST /orders creates.")
        texts = " ".join(c.text for c in model.context or [])
        assert "POST /orders creates." in texts
        assert self.ENDPOINT_TEXT not in texts

    def test_deleted_content_is_not_used_for_grounding(self, grounded):
        client, pid, model = grounded
        sid = create(client, pid, title="Users", content=self.ENDPOINT_TEXT).get_json()["id"]
        assert client.delete(url(pid, f"/{sid}")).status_code == 204
        _ask(client, pid, self.ENDPOINT_TEXT)
        assert not any(self.ENDPOINT_TEXT in c.text for c in (model.context or []))


# --------------------------------------------------------------------------- Security


class TestSecurity:
    def test_script_content_is_returned_as_inert_json(self, client, pid):
        script = "<script>alert('xss')</script>"
        sid = create(client, pid, title="XSS Test", content=script).get_json()["id"]
        res = client.get(url(pid, f"/{sid}"))
        assert res.mimetype == "application/json"
        assert res.get_json()["content"] == script
        assert res.headers.get("X-Content-Type-Options", "nosniff") == "nosniff"

    def test_injection_attempts_are_neutralized(self, client, pid):
        create(client, pid, content="keep me")
        before = client.get(url(pid)).get_json()
        res = client.get(
            f"{BASE}/search", query_string={"projectId": pid, "q": "'; DROP TABLE text_content; --"}
        )
        assert res.status_code == 200
        assert client.get(url(pid)).get_json() == before

    def test_rate_limit_response_says_when_to_retry(self, limited_app):
        client, pid = _register(limited_app, "rl@example.com")
        responses = [create(client, pid) for _ in range(31)]
        limited = next(r for r in responses if r.status_code == 429)
        assert int(limited.headers["Retry-After"]) >= 1
