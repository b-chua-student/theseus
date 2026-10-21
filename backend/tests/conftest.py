import pytest

from application.app import create_app, limiter
from repositories.manuscript.fake_manuscript_repository import (
    FakeManuscriptRepository,
)
from repositories.revision_history.fake_revision_history_repository import (
    FakeRevisionHistoryRepository,
)


@pytest.fixture
def manuscript_repo():
    return FakeManuscriptRepository(seed=True)


@pytest.fixture
def revision_history_repo():
    return FakeRevisionHistoryRepository()


@pytest.fixture
def app(manuscript_repo, revision_history_repo):
    return create_app(
        config={"TESTING": True, "RATELIMIT_ENABLED": False},
        manuscript_repo=manuscript_repo,
        revision_history_repo=revision_history_repo,
    )


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def limited_app(manuscript_repo, revision_history_repo):
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
def limited_client(limited_app):
    return limited_app.test_client()
