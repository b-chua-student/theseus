"""Flask-client tests for the /api/sources/text endpoints."""

from uuid import uuid4

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

BASE = "/api/sources/text"


def _signed_in_client(app, email):
    client = app.test_client()
    res = client.post(
        "/api/auth/register",
        json={"display_name": "Tester", "email": email, "password": "correct-horse-battery"},
    )
    assert res.status_code == 201
    client.post("/api/projects", json={"project_name": "P"})
    project_id = client.get("/api/projects").get_json()[0]["id"]
    return client, project_id


@pytest.fixture
def ctx(app):
    client, project_id = _signed_in_client(app, "a@example.com")
    return client, project_id


@pytest.fixture
def client(ctx):
    return ctx[0]


@pytest.fixture
def pid(ctx):
    return ctx[1]


def url(pid, path="", **params):
    qs = "&".join([f"projectId={pid}"] + [f"{k}={v}" for k, v in params.items()])
    return f"{BASE}{path}?{qs}"


def create(client, pid, **overrides):
    body = {"title": "Title", "content": "Hello world"} | overrides
    return client.post(url(pid), json=body)


def error_fields(res):
    return {e["field"] for e in res.get_json()["errors"]}


class TestRoutePrefix:
    def test_base_path_matches_frontend_client(self, app):
        rules = {r.rule for r in app.url_map.iter_rules()}
        assert "/api/sources/text" in rules
        assert "/api/sources/text/search" in rules
        assert "/api/sources/text/<source_id>" in rules


class TestAuth:
    @pytest.mark.parametrize(
        "method,path",
        [
            ("post", ""),
            ("get", ""),
            ("get", "/search"),
            ("get", f"/{uuid4()}"),
            ("put", f"/{uuid4()}"),
            ("delete", f"/{uuid4()}"),
        ],
    )
    def test_401_without_login(self, app, method, path):
        res = getattr(app.test_client(), method)(url(uuid4(), path))
        assert res.status_code == 401

    def test_foreign_project_is_404_for_every_endpoint(self, app, client, pid):
        sid = create(client, pid).get_json()["id"]
        other, _ = _signed_in_client(app, "b@example.com")
        calls = [
            other.post(url(pid), json={"title": "t", "content": "c"}),
            other.get(url(pid)),
            other.get(url(pid, "/search", q="x")),
            other.get(url(pid, f"/{sid}")),
            other.put(url(pid, f"/{sid}"), json={"title": "t", "content": "c"}),
            other.delete(url(pid, f"/{sid}")),
        ]
        assert [r.status_code for r in calls] == [404] * 6
        # nothing was changed or removed
        assert client.get(url(pid, f"/{sid}")).get_json()["version"] == 1

    def test_source_of_another_project_is_404(self, app, client, pid):
        sid = create(client, pid).get_json()["id"]
        other, other_pid = _signed_in_client(app, "b@example.com")
        assert other.get(url(other_pid, f"/{sid}")).status_code == 404
        assert other.delete(url(other_pid, f"/{sid}")).status_code == 404
        assert other.get(url(other_pid)).get_json()["items"] == []

    def test_project_id_required_and_validated(self, client):
        assert error_fields(client.get(BASE)) == {"projectId"}
        assert error_fields(client.get(f"{BASE}?projectId=nope")) == {"projectId"}
        assert client.get(f"{BASE}?projectId={uuid4()}").status_code == 404


class TestCreate:
    def test_library_list_identifies_text_sources(self, client, pid):
        created = create(client, pid)
        assert created.status_code == 201
        sources = client.get(f"/api/sources?projectId={pid}").get_json()
        source = next(s for s in sources if s["id"] == created.get_json()["id"])
        assert source["kind"] == "text"

    def test_minimal_create(self, client, pid):
        res = create(client, pid)
        assert res.status_code == 201
        body = res.get_json()
        assert body["kind"] == "text"
        assert body["version"] == 1
        assert body["contentType"] == "other"
        assert body["tags"] == []
        assert body["content"] == "Hello world"
        assert "snippet" not in body

    def test_full_create_normalizes_metadata(self, client, pid):
        res = create(
            client,
            pid,
            title="  Notes  ",
            description=" d ",
            tags=[" a ", "a", "", "b"],
            contentType="notes",
        )
        body = res.get_json()
        assert (body["title"], body["description"], body["tags"], body["contentType"]) == (
            "Notes",
            "d",
            ["a", "b"],
            "notes",
        )

    @pytest.mark.parametrize(
        "overrides,field",
        [
            ({"title": ""}, "title"),
            ({"title": "   "}, "title"),
            ({"title": "x" * 201}, "title"),
            ({"content": ""}, "content"),
            ({"content": "   "}, "content"),
            ({"content": "x" * 100_001}, "content"),
            ({"description": "x" * 1001}, "description"),
            ({"tags": [str(i) for i in range(11)]}, "tags"),
            ({"contentType": "poem"}, "contentType"),
            ({"contentType": ""}, "contentType"),
            ({"title": 5}, "title"),
        ],
    )
    def test_invalid_fields_return_400_and_persist_nothing(self, client, pid, overrides, field):
        res = create(client, pid, **overrides)
        assert res.status_code == 400
        assert field in error_fields(res)
        for e in res.get_json()["errors"]:
            assert isinstance(e["message"], str) and e["message"]
        assert client.get(url(pid)).get_json()["total"] == 0

    def test_missing_fields_report_each_field(self, client, pid):
        res = client.post(url(pid), json={})
        assert error_fields(res) == {"title", "content"}

    def test_non_json_body_is_400(self, client, pid):
        res = client.post(url(pid), data="not json", content_type="text/plain")
        assert res.status_code == 400

    @pytest.mark.parametrize("n", [1, 100_000])
    def test_content_boundaries_accepted(self, client, pid, n):
        assert create(client, pid, content="x" * n).status_code == 201

    def test_boundary_title_description_tags_accepted(self, client, pid):
        res = create(
            client,
            pid,
            title="t" * 200,
            description="d" * 1000,
            tags=[str(i) for i in range(10)],
        )
        assert res.status_code == 201

    def test_content_round_trips_verbatim(self, client, pid):
        text = '  <script>alert(1)</script>\n\t{"$ne": null} héllo 日本 😀  \n'
        sid = create(client, pid, content=text).get_json()["id"]
        assert client.get(url(pid, f"/{sid}")).get_json()["content"] == text

    def test_oversized_body_is_413(self, client, pid):
        res = client.post(url(pid), data="x" * (512 * 1024 + 1), content_type="application/json")
        assert res.status_code == 413


class TestRead:
    def test_get_detail_includes_content(self, client, pid):
        sid = create(client, pid).get_json()["id"]
        body = client.get(url(pid, f"/{sid}")).get_json()
        assert body["content"] == "Hello world"
        assert body["id"] == sid

    def test_unknown_and_malformed_ids_are_404(self, client, pid):
        assert client.get(url(pid, f"/{uuid4()}")).status_code == 404
        assert client.get(url(pid, "/not-a-uuid")).status_code == 404

    def test_removed_source_is_404(self, client, pid):
        sid = create(client, pid).get_json()["id"]
        assert client.delete(url(pid, f"/{sid}")).status_code == 204
        assert client.get(url(pid, f"/{sid}")).status_code == 404
        assert (
            client.put(url(pid, f"/{sid}"), json={"title": "t", "content": "c"}).status_code == 404
        )
        assert client.delete(url(pid, f"/{sid}")).status_code == 404

    def test_file_source_is_not_exposed_via_text_routes(self, app, client, pid):
        res = client.post(
            "/api/sources", json={"title": "F", "file_ref": "f.pdf", "project_id": pid}
        )
        sid = res.get_json()["id"]
        assert client.get(url(pid, f"/{sid}")).status_code == 404
        assert (
            client.put(url(pid, f"/{sid}"), json={"title": "t", "content": "c"}).status_code == 404
        )
        assert client.delete(url(pid, f"/{sid}")).status_code == 404


class TestList:
    def test_envelope_snippet_and_no_content(self, client, pid):
        create(client, pid, content="y" * 500)
        body = client.get(url(pid)).get_json()
        assert (body["total"], body["page"], body["pageSize"]) == (1, 1, 20)
        item = body["items"][0]
        assert item["snippet"] == "y" * 200
        assert "content" not in item

    def test_filters_sort_and_paging(self, client, pid):
        create(client, pid, title="b", contentType="code", tags=["x"])
        create(client, pid, title="A", contentType="notes", tags=["x", "y"])
        create(client, pid, title="c", contentType="notes")

        def titles(**p):
            return [i["title"] for i in client.get(url(pid, **p)).get_json()["items"]]

        assert titles(contentType="notes", sort="title") == ["A", "c"]
        assert titles(tag="y") == ["A"]
        assert titles(sort="title") == ["A", "b", "c"]
        assert titles(sort="updatedAt") == ["c", "A", "b"]
        paged = client.get(url(pid, sort="title", pageSize=2, page=2)).get_json()
        assert [i["title"] for i in paged["items"]] == ["c"]
        assert (paged["total"], paged["page"], paged["pageSize"]) == (3, 2, 2)

    def test_page_size_capped_at_100(self, client, pid):
        assert client.get(url(pid, pageSize=500)).get_json()["pageSize"] == 100

    @pytest.mark.parametrize(
        "params,field",
        [
            ({"contentType": "poem"}, "contentType"),
            ({"sort": "random"}, "sort"),
            ({"page": "abc"}, "page"),
            ({"pageSize": "abc"}, "pageSize"),
        ],
    )
    def test_invalid_query_is_400(self, client, pid, params, field):
        res = client.get(url(pid, **params))
        assert res.status_code == 400
        assert error_fields(res) == {field}

    def test_excludes_removed(self, client, pid):
        sid = create(client, pid).get_json()["id"]
        client.delete(url(pid, f"/{sid}"))
        assert client.get(url(pid)).get_json()["total"] == 0

    def test_existing_library_list_still_works(self, client, pid):
        create(client, pid)
        assert client.get("/api/sources").status_code == 200


class TestSearch:
    def test_matches_content_and_title_and_isolated(self, app, client, pid):
        create(client, pid, title="Rate limiting", content="alpha")
        create(client, pid, title="Other", content="the quick brown fox")
        other, other_pid = _signed_in_client(app, "b@example.com")
        create(other, other_pid, title="Fox elsewhere", content="fox")

        def titles(c, p, q, **kw):
            res = c.get(url(p, "/search", q=q, **kw))
            assert res.status_code == 200
            return [i["title"] for i in res.get_json()["items"]]

        assert titles(client, pid, "fox") == ["Other"]
        assert titles(client, pid, "limiting") == ["Rate limiting"]
        assert titles(client, pid, "fox", contentType="code") == []
        assert titles(other, other_pid, "fox") == ["Fox elsewhere"]

    def test_empty_result_is_200(self, client, pid):
        body = client.get(url(pid, "/search", q="zzz")).get_json()
        assert body == {"items": [], "total": 0, "page": 1, "pageSize": 20}

    def test_search_not_shadowed_by_id_route(self, client, pid):
        assert client.get(url(pid, "/search", q="x")).status_code == 200

    def test_q_required_and_filters_validated(self, client, pid):
        assert error_fields(client.get(url(pid, "/search"))) == {"q"}
        assert error_fields(client.get(url(pid, "/search", q="x", contentType="poem"))) == {
            "contentType"
        }

    def test_query_syntax_is_not_interpreted(self, client, pid):
        create(client, pid, content="plain")
        for q in ['{"$ne":1}', ".*", "'; drop", "<b>"]:
            res = client.get(f"{BASE}/search", query_string={"projectId": pid, "q": q})
            assert res.status_code == 200, q
            assert res.get_json()["total"] == 0


class TestUpdate:
    def test_put_replaces_fields_and_bumps_version(self, client, pid):
        sid = create(client, pid, tags=["a"], description="d").get_json()["id"]
        res = client.put(
            url(pid, f"/{sid}"),
            json={"title": "New", "content": "new body", "contentType": "code"},
        )
        assert res.status_code == 200
        body = res.get_json()
        assert (body["title"], body["content"], body["contentType"]) == ("New", "new body", "code")
        assert body["description"] is None and body["tags"] == []
        assert body["version"] == 2
        assert client.get(url(pid, f"/{sid}")).get_json()["version"] == 2

    def test_invalid_update_changes_nothing(self, client, pid):
        sid = create(client, pid).get_json()["id"]
        res = client.put(url(pid, f"/{sid}"), json={"title": "", "content": "x" * 100_001})
        assert res.status_code == 400
        assert error_fields(res) == {"title", "content"}
        body = client.get(url(pid, f"/{sid}")).get_json()
        assert (body["version"], body["title"]) == (1, "Title")

    def test_invalid_content_type_rejected_not_mapped_to_other(self, client, pid):
        sid = create(client, pid, contentType="code").get_json()["id"]
        res = client.put(
            url(pid, f"/{sid}"), json={"title": "t", "content": "c", "contentType": "bogus"}
        )
        assert res.status_code == 400
        assert client.get(url(pid, f"/{sid}")).get_json()["contentType"] == "code"

    def test_unknown_id_is_404(self, client, pid):
        res = client.put(url(pid, f"/{uuid4()}"), json={"title": "t", "content": "c"})
        assert res.status_code == 404

    def test_oversized_body_is_413(self, client, pid):
        sid = create(client, pid).get_json()["id"]
        res = client.put(
            url(pid, f"/{sid}"), data="x" * (512 * 1024 + 1), content_type="application/json"
        )
        assert res.status_code == 413


class TestDelete:
    def test_delete_is_soft_and_returns_204(self, app, client, pid):
        sid = create(client, pid).get_json()["id"]
        res = client.delete(url(pid, f"/{sid}"))
        assert res.status_code == 204 and res.data == b""
        from domain.src_lib.models.value_objects import SourceId

        stored = app.extensions["container"].source.get.execute(source_id=sid)
        assert stored is not None and stored.is_removed
        assert SourceId.from_str(sid) == stored.id


class TestRateLimit:
    def test_write_endpoints_return_429_with_retry_after(self, limited_app):
        client, pid = _signed_in_client(limited_app, "a@example.com")
        responses = [create(client, pid) for _ in range(31)]
        assert responses[0].status_code == 201
        limited = [r for r in responses if r.status_code == 429]
        assert limited
        assert int(limited[0].headers["Retry-After"]) >= 1
        assert "error" in limited[0].get_json()


@settings(max_examples=40, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    content=st.text(min_size=1, max_size=300).filter(lambda s: s.strip()),
)
def test_property_content_round_trips_byte_for_byte(app, content):
    """**Validates: Requirements 1.1, 3.1, N5**"""
    client, pid = _signed_in_client(app, f"{uuid4().hex}@example.com")
    res = create(client, pid, content=content)
    assert res.status_code == 201
    sid = res.get_json()["id"]
    assert client.get(url(pid, f"/{sid}")).get_json()["content"] == content
