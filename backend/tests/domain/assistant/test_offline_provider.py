import socket
from unittest.mock import Mock

import pytest
from google.genai import types

from domain.assistant.infrastructure.adapters.gemini_chat_model import GeminiChatModel
from domain.assistant.models.value_objects import Query


def test_s014_offline_provider_captures_request(offline_provider: Mock) -> None:
    adapter = GeminiChatModel(model="offline-model")
    assert offline_provider.call_args.kwargs["api_key"] == "offline-test-key"

    with (
        socket.socket() as connection,
        pytest.raises(AssertionError, match="Network access is disabled"),
    ):
        connection.connect(("127.0.0.1", 443))

    answer = adapter.reply([], Query("What is a primary source?"))
    generate = offline_provider.return_value.models.generate_content
    generate.assert_called_once()
    request = generate.call_args.kwargs
    assert request["model"] == "offline-model"
    assert isinstance(request["config"], types.GenerateContentConfig)
    (turn,) = request["contents"]
    assert turn.role == "user"
    assert turn.parts[0].text == "What is a primary source?"
    assert answer.text == "Offline reply."
