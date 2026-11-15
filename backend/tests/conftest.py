from collections.abc import Iterator

import pytest
from flask import Flask
from flask.testing import FlaskClient

from bootstrap.app import create_app
from bootstrap.extensions import limiter


@pytest.fixture
def app() -> Flask:
    """Create a Flask app in testing mode with rate limiting disabled.

    Args:
        manuscript_repo (FakeManuscriptRepository): Injected manuscript repository.
        revision_history_repo (FakeRevisionHistoryRepository): Injected
            revision history repository.

    Returns:
        Flask: Configured application instance.
    """
    return create_app(
        config={"TESTING": True, "SECRET_KEY": "test-secret", "RATELIMIT_ENABLED": False},
    )


@pytest.fixture
def client(app) -> FlaskClient:
    """Provide a test client for the rate-limit-free app.

    Args:
        app (Flask): Application with rate limiting disabled.

    Returns:
        FlaskClient: Test client bound to ``app``.
    """
    return app.test_client()


@pytest.fixture
def limited_app() -> Iterator[Flask]:
    """Create a Flask app with rate limiting enabled.

    Uses in-memory limiter storage and resets limiter state before and
    after the test.

    Args:
        manuscript_repo (FakeManuscriptRepository): Injected manuscript repository.
        revision_history_repo (FakeRevisionHistoryRepository): Injected
            revision history repository.

    Yields:
        Flask: Configured application instance with rate limiting active.
    """
    app = create_app(
        config={
            "TESTING": True,
            "RATELIMIT_ENABLED": True,
            "SECRET_KEY": "test-secret",
            "RATELIMIT_STORAGE_URI": "memory://",
        },
    )
    limiter.reset()
    yield app
    limiter.reset()


@pytest.fixture
def limited_client(limited_app) -> FlaskClient:
    """Provide a test client for the rate-limited app.

    Args:
        limited_app (Flask): Application with rate limiting enabled.

    Returns:
        FlaskClient: Test client bound to ``limited_app``.
    """
    return limited_app.test_client()


@pytest.fixture
def user_payload():
    return {
        "display_name": "Test User",
        "email": "user@example.com",
        "password": "correct-horse-battery",
    }


@pytest.fixture
def registered_user(client, user_payload):
    client.post("/api/auth/register", json=user_payload)
    client.post("/api/auth/logout")
    return user_payload
