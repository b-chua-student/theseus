"""Offline chat submission burst tests through the application factory."""

import time
from unittest.mock import Mock

import pytest

from bootstrap.app import create_app
from bootstrap.container import build_container
from domain.assistant.infrastructure.adapters.gemini_chat_model import GeminiChatModel


@pytest.mark.integration
@pytest.mark.parametrize(
    "enable_limit", [pytest.param(True, id="s012_enabled"), pytest.param(False, id="s018_default")]
)
def test_chat_submission_burst(
    offline_provider: Mock, monkeypatch: pytest.MonkeyPatch, *, enable_limit: bool
) -> None:
    config = {"TESTING": True}
    if enable_limit:
        config["RATELIMIT_ENABLED"] = True
    container = build_container(chat_model=GeminiChatModel(model="offline-model"))
    client = create_app(config, container).test_client()
    registration = client.post(
        "/api/auth/register",
        json={
            "display_name": "Writer",
            "email": "writer@example.com",
            "password": "Example-password-42",
        },
    )
    assert registration.status_code == 201
    assert client.post("/api/projects", json={"project_name": "Research"}).status_code == 201
    project_id = client.get("/api/projects").get_json()[0]["id"]
    conversations = f"/api/projects/{project_id}/conversations"
    started = client.post(conversations)
    assert started.status_code == 201
    url = f"{conversations}/{started.get_json()['id']}/exchanges"

    now = time.time()
    monkeypatch.setattr(time, "time", lambda: now)
    responses = [
        client.post(url, json={"query": f"Research question {i}?", "context_scope": "none"})
        for i in range(1, 12)
    ]

    accepted = 10 if enable_limit else 11
    for response in responses[:accepted]:
        assert response.status_code == 201
        assert response.get_json()["answer"] == "Offline reply."
    if enable_limit:
        assert responses[-1].status_code == 429
    generate = offline_provider.return_value.models.generate_content
    assert generate.call_count == accepted
