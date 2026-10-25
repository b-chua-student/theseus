from collections.abc import Iterator

import pytest
from flask import Flask
from flask.testing import FlaskClient

from api.app import create_app, limiter
from repositories.manuscript.fake_manuscript_repository import (
    FakeManuscriptRepository,
)
from repositories.manuscript.manuscript_repository import ManuscriptRepository
from repositories.revision_history.fake_revision_history_repository import (
    FakeRevisionHistoryRepository,
)
from repositories.revision_history.revision_history_repository import RevisionHistoryRepository


@pytest.fixture
def manuscript_repo() -> ManuscriptRepository:
    """Provide a seeded in-memory manuscript repository.

    Returns:
        FakeManuscriptRepository: Fake repository pre-populated with seed data.
    """
    return FakeManuscriptRepository(seed=True)


@pytest.fixture
def bare_manuscript_repo() -> ManuscriptRepository:
    """Provide an empty in-memory manuscript repository.

    Returns:
        FakeManuscriptRepository: Fake repository with no manuscripts.
    """
    return FakeManuscriptRepository(seed=False)


@pytest.fixture
def revision_history_repo() -> RevisionHistoryRepository:
    """Provide an empty in-memory revision history repository.

    Returns:
        FakeRevisionHistoryRepository: Fake repository with no revisions.
    """
    return FakeRevisionHistoryRepository()


@pytest.fixture
def app(manuscript_repo, revision_history_repo) -> Flask:
    """Create a Flask app in testing mode with rate limiting disabled.

    Args:
        manuscript_repo (FakeManuscriptRepository): Injected manuscript repository.
        revision_history_repo (FakeRevisionHistoryRepository): Injected
            revision history repository.

    Returns:
        Flask: Configured application instance.
    """
    return create_app(
        config={"TESTING": True, "RATELIMIT_ENABLED": False},
        manuscript_repo=manuscript_repo,
        revision_history_repo=revision_history_repo,
    )


@pytest.fixture
def bare_app(bare_manuscript_repo, revision_history_repo) -> Flask:
    """Create a Flask app with an empty manuscript repository.

    Testing mode with rate limiting disabled.

    Args:
        bare_manuscript_repo (FakeManuscriptRepository): Injected empty
            manuscript repository.
        revision_history_repo (FakeRevisionHistoryRepository): Injected
            revision history repository.

    Returns:
        Flask: Configured application instance.
    """
    return create_app(
        config={"TESTING": True, "RATELIMIT_ENABLED": False},
        manuscript_repo=bare_manuscript_repo,
        revision_history_repo=revision_history_repo,
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
def limited_app(manuscript_repo, revision_history_repo) -> Iterator[Flask]:
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
            "RATELIMIT_STORAGE_URI": "memory://",
        },
        manuscript_repo=manuscript_repo,
        revision_history_repo=revision_history_repo,
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
