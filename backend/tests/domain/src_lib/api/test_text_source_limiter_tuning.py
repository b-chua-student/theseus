"""Limiter thresholds for the text endpoints (R9 tuning, task 9).

The app-wide default (20/hour per IP) must not throttle reading or deleting text
sources, and the write limit must tolerate a burst of 20 users behind one IP.
"""

BASE = "/api/sources/text"


def _signed_in(app, email):
    client = app.test_client()
    client.post(
        "/api/auth/register",
        json={"display_name": "T", "email": email, "password": "correct-horse-battery"},
    )
    client.post("/api/projects", json={"project_name": "P"})
    return client, client.get("/api/projects").get_json()[0]["id"]


def test_reads_are_not_capped_by_the_hourly_default(limited_app):
    client, pid = _signed_in(limited_app, "r@example.com")
    statuses = {client.get(f"{BASE}?projectId={pid}").status_code for _ in range(30)}
    assert statuses == {200}


def test_twenty_creates_from_one_ip_are_allowed(limited_app):
    client, pid = _signed_in(limited_app, "w@example.com")
    statuses = [
        client.post(f"{BASE}?projectId={pid}", json={"title": f"t{i}", "content": "c"}).status_code
        for i in range(20)
    ]
    assert statuses == [201] * 20
