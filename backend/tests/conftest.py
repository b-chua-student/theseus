from collections.abc import Iterator

import pytest
from flask import Flask
from flask.testing import FlaskClient

from api.app import create_app, limiter
from domain.project.aggregates import Project
from domain.user.aggregates import User
from repositories.manuscript.fake_manuscript_repository import (
    FakeManuscriptRepository,
)
from repositories.manuscript.manuscript_repository import ManuscriptRepository
from repositories.project.fake_project_repository import FakeProjectRepository
from repositories.project.project_repository import ProjectRepository
from repositories.revision_history.fake_revision_history_repository import (
    FakeRevisionHistoryRepository,
)
from repositories.revision_history.revision_history_repository import RevisionHistoryRepository
from repositories.user.fake_user_repository import FakeUserRepository
from repositories.user.user_repository import UserRepository


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
def user_repo() -> UserRepository:
    """Provide a seeded in-memory user repository.

    Returns:
        FakeUserRepository: Fake repository pre-populated with the sample owner.
    """
    return FakeUserRepository(seed=True)


@pytest.fixture
def bare_user_repo() -> UserRepository:
    """Provide an empty in-memory user repository.

    Returns:
        FakeUserRepository: Fake repository with no users.
    """
    return FakeUserRepository(seed=False)


@pytest.fixture
def project_repo() -> ProjectRepository:
    """Provide a seeded in-memory project repository.

    Returns:
        FakeProjectRepository: Fake repository pre-populated with the sample project.
    """
    return FakeProjectRepository(seed=True)


@pytest.fixture
def bare_project_repo() -> ProjectRepository:
    """Provide an empty in-memory project repository.

    Returns:
        FakeProjectRepository: Fake repository with no projects.
    """
    return FakeProjectRepository(seed=False)


@pytest.fixture
def user(user_repo: UserRepository) -> User:
    """Provide the seeded sample user.

    Args:
        user_repo (UserRepository): Seeded user repository.

    Returns:
        User: The pre-populated sample owner.
    """
    return user_repo.get_by_id(FakeUserRepository.OWNER_ID)  # type: ignore[return-value]


@pytest.fixture
def project(project_repo: ProjectRepository) -> Project:
    """Provide the seeded sample project.

    Args:
        project_repo (ProjectRepository): Seeded project repository.

    Returns:
        Project: The pre-populated sample project.
    """
    return project_repo.get_by_id(FakeProjectRepository.PROJECT_ID)  # type: ignore[return-value]


@pytest.fixture
def app(manuscript_repo, revision_history_repo, user_repo, project_repo) -> Flask:
    """Create a Flask app in testing mode with rate limiting disabled.

    Args:
        manuscript_repo (FakeManuscriptRepository): Injected manuscript repository.
        revision_history_repo (FakeRevisionHistoryRepository): Injected
            revision history repository.
        user_repo (FakeUserRepository): Injected user repository.
        project_repo (FakeProjectRepository): Injected project repository.

    Returns:
        Flask: Configured application instance.
    """
    return create_app(
        config={"TESTING": True, "RATELIMIT_ENABLED": False},
        manuscript_repo=manuscript_repo,
        revision_history_repo=revision_history_repo,
        user_repo=user_repo,
        project_repo=project_repo,
    )


@pytest.fixture
def bare_app(
    bare_manuscript_repo, revision_history_repo, bare_user_repo, bare_project_repo
) -> Flask:
    """Create a Flask app with empty repositories.

    Testing mode with rate limiting disabled.

    Args:
        bare_manuscript_repo (FakeManuscriptRepository): Injected empty
            manuscript repository.
        revision_history_repo (FakeRevisionHistoryRepository): Injected
            revision history repository.
        bare_user_repo (FakeUserRepository): Injected empty user repository.
        bare_project_repo (FakeProjectRepository): Injected empty project repository.

    Returns:
        Flask: Configured application instance.
    """
    return create_app(
        config={"TESTING": True, "RATELIMIT_ENABLED": False},
        manuscript_repo=bare_manuscript_repo,
        revision_history_repo=revision_history_repo,
        user_repo=bare_user_repo,
        project_repo=bare_project_repo,
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
def limited_app(manuscript_repo, revision_history_repo, user_repo, project_repo) -> Iterator[Flask]:
    """Create a Flask app with rate limiting enabled.

    Uses in-memory limiter storage and resets limiter state before and
    after the test.

    Args:
        manuscript_repo (FakeManuscriptRepository): Injected manuscript repository.
        revision_history_repo (FakeRevisionHistoryRepository): Injected
            revision history repository.
        user_repo (FakeUserRepository): Injected user repository.
        project_repo (FakeProjectRepository): Injected project repository.

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
        user_repo=user_repo,
        project_repo=project_repo,
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
