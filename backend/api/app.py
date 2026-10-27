from flask import Flask

from api.routes.manuscript import manuscripts_bp
from repositories.manuscript.fake_manuscript_repository import (
    FakeManuscriptRepository,
)
from repositories.manuscript.manuscript_repository import ManuscriptRepository
from repositories.revision_history.fake_revision_history_repository import (
    FakeRevisionHistoryRepository,
)
from repositories.revision_history.revision_history_repository import RevisionHistoryRepository
from services.manuscript.create_manuscript import CreateManuscriptService
from services.manuscript.delete_manuscript import DeleteManuscriptService
from services.manuscript.get_all_manuscript import GetAllManuscriptService
from services.manuscript.get_manuscript import GetManuscriptService
from services.manuscript.update_manuscript import UpdateManuscriptService

from .extensions import limiter


def create_app(
    config: dict | None = None,
    manuscript_repo: ManuscriptRepository | None = None,
    revision_history_repo: RevisionHistoryRepository | None = None,
) -> Flask:
    """Create and configure the Flask application.

    Initializes the rate limiter, registers the manuscripts blueprint, and
    wires up the manuscript services into ``app.extensions``.

    Args:
        config: Optional configuration values applied to ``app.config``.
        manuscript_repo: Repository for manuscript persistence. Defaults to a
            seeded ``FakeManuscriptRepository``.
        revision_history_repo: Repository for revision history. Defaults to a
            ``FakeRevisionHistoryRepository``.

    Returns:
        The configured Flask application instance.
    """
    app = Flask(__name__)
    app.config.update(config or {})
    limiter.init_app(app)

    app.register_blueprint(manuscripts_bp, url_prefix="/api/manuscripts")

    if manuscript_repo is None:
        manuscript_repo = FakeManuscriptRepository(seed=True)
    if revision_history_repo is None:
        revision_history_repo = FakeRevisionHistoryRepository()

    create_manuscript_service = CreateManuscriptService(repository=manuscript_repo)

    app.extensions["create_manuscript_service"] = create_manuscript_service

    get_all_manuscripts_service = GetAllManuscriptService(repository=manuscript_repo)

    app.extensions["get_all_manuscripts_service"] = get_all_manuscripts_service

    get_manuscript_service = GetManuscriptService(repository=manuscript_repo)

    app.extensions["get_manuscript_service"] = get_manuscript_service

    delete_manuscript_service = DeleteManuscriptService(manuscript_repo)

    app.extensions["delete_manuscript_service"] = delete_manuscript_service

    update_manuscript_service = UpdateManuscriptService(repository=manuscript_repo)

    app.extensions["update_manuscript_service"] = update_manuscript_service

    return app
