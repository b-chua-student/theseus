import socket
from typing import NoReturn
from unittest.mock import Mock

import pytest

from domain.assistant.infrastructure.adapters import gemini_chat_model


@pytest.fixture
def offline_provider(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Capture Gemini requests and keep synchronous provider I/O offline."""

    def block_network(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Network access is disabled for offline provider tests")

    monkeypatch.setattr(socket, "getaddrinfo", block_network)
    monkeypatch.setattr(socket.socket, "connect", block_network)
    monkeypatch.setattr(socket.socket, "connect_ex", block_network)
    monkeypatch.setattr(gemini_chat_model, "load_dotenv", lambda: None)
    monkeypatch.setenv("GEMINI_API_KEY", "offline-test-key")
    client_factory = Mock()
    client_factory.return_value.models.generate_content.return_value.text = "Offline reply."
    monkeypatch.setattr(gemini_chat_model.genai, "Client", client_factory)
    return client_factory
