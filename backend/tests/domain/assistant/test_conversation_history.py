from uuid import uuid4

import pytest

from bootstrap.app import create_app
from bootstrap.container import build_container
from domain.assistant.infrastructure.adapters.in_memory_conversation_repository import (
    InMemoryConversationRepository,
)
from domain.assistant.models.errors import ConversationNotFoundError
from domain.assistant.models.value_objects import Answer, ProjectId
from domain.assistant.services.chat import ChatService


class RecordingModel:
    def reply(self, history, query, context=None):
        return Answer("ok")


def test_history_survives_service_recreation_and_is_project_scoped():
    repo = InMemoryConversationRepository()
    service = ChatService(repo, RecordingModel())
    project = str(ProjectId.new().value)
    other = str(ProjectId.new().value)
    cid = str(service.start(project).value)
    service.start(other)
    service.ask(cid, "Remember this", context_scope="none", project_id=project)
    restored = ChatService(repo, RecordingModel())
    assert [str(c.id.value) for c in restored.list(project)] == [cid]
    conversation = restored.get(project, cid)
    assert conversation.history[0].query.text == "Remember this"
    assert conversation.history[0].answer.text == "ok"
    assert conversation.context_scope == "none"
    with pytest.raises(ConversationNotFoundError):
        restored.get(other, cid)
    with pytest.raises(ConversationNotFoundError):
        restored.ask(cid, "wrong project", project_id=other)
    assert len(conversation.history) == 1


def test_history_routes_require_project_access_and_return_exchanges():
    from types import SimpleNamespace

    owner = str(uuid4())
    pid = str(uuid4())
    project = SimpleNamespace(owner=SimpleNamespace(id=SimpleNamespace(value=owner)), members=[])
    service = ChatService(InMemoryConversationRepository(), RecordingModel())
    container = build_container(chat_model=RecordingModel())
    app = create_app(
        config={"TESTING": True, "SECRET_KEY": "test", "RATELIMIT_ENABLED": False},
        container=container,
    )
    app.extensions["container"] = SimpleNamespace(
        project=SimpleNamespace(get=SimpleNamespace(execute=lambda **kwargs: project)),
        assistant=SimpleNamespace(chat=service),
    )
    client = app.test_client()
    url = f"/api/projects/{pid}/conversations"
    assert client.get(url).status_code == 401
    with client.session_transaction() as session:
        session["user_id"] = owner
    cid = client.post(url).get_json()["id"]
    assert (
        client.post(
            f"{url}/{cid}/exchanges", json={"query": "Hello", "context_scope": "none"}
        ).status_code
        == 201
    )
    assert client.get(url).get_json()[0]["title"] == "Hello"
    detail = client.get(f"{url}/{cid}").get_json()
    assert detail["exchanges"][0]["answer"] == "ok"
    assert detail["context_scope"] == "none"
    assert client.get(f"/api/projects/{uuid4()}/conversations/{cid}").status_code == 404
    with client.session_transaction() as session:
        session["user_id"] = str(uuid4())
    assert client.get(url).status_code == 404
    assert client.get(f"{url}/{cid}").status_code == 404


def test_mongo_round_trip_preserves_context_and_reads_legacy_documents():
    from domain.assistant.infrastructure.adapters.mongodb_conversation_repository import (
        MongoConversationRepository,
    )
    from domain.assistant.models.aggregates import Conversation

    conversation = Conversation.start(ProjectId.new())
    conversation.context_scope = "source_library"
    conversation.source_ids = [str(uuid4())]
    doc = MongoConversationRepository._to_doc(conversation)
    restored = MongoConversationRepository._to_conversation(doc)
    assert restored.source_ids == conversation.source_ids
    assert restored.context_scope == "source_library"
    del doc["context_scope"]
    del doc["source_ids"]
    legacy = MongoConversationRepository._to_conversation(doc)
    assert legacy.context_scope == "source_library"
    assert legacy.source_ids is None
