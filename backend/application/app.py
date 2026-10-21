from flask import Flask

from application.routes.manuscripts import manuscripts_bp
from repositories.manuscript.fake_manuscript_repository import (
    FakeManuscriptRepository,
)
from repositories.revision_history.fake_revision_history_repository import (
    FakeRevisionHistoryRepository,
)
from services.manuscript.create_manuscript import CreateManuscriptService
from services.manuscript.get_all_manuscript import GetAllManuscriptService
from services.manuscript.get_manuscript import GetManuscriptService
from services.manuscript.delete_manuscript import DeleteManuscriptService
from services.manuscript.create_manuscript import CreateManuscriptService

from .extensions import limiter


def create_app(
    config: dict | None = None,
    manuscript_repo=None,
    revision_history_repo=None,
) -> Flask:
    app = Flask(__name__)
    app.config.update(config or {})
    limiter.init_app(app)

    app.register_blueprint(manuscripts_bp, url_prefix="/api/manuscripts")

    if manuscript_repo is None:
        manuscript_repo = FakeManuscriptRepository(seed=True)
    if revision_history_repo is None:
        revision_history_repo = FakeRevisionHistoryRepository()

    create_manuscript_service = CreateManuscriptService(
        manuscript_repo=manuscript_repo, revision_history_repo=revision_history_repo
    )

    app.extensions["create_manuscript_service"] = create_manuscript_service

    get_all_manuscripts_service = GetAllManuscriptService(repository=manuscript_repo)

    app.extensions["get_all_manuscripts_service"] = get_all_manuscripts_service

    get_manuscript_service = GetManuscriptService(repository=manuscript_repo)

    app.extensions["get_manuscript_service"] = get_manuscript_service

    delete_manuscript_service = DeleteManuscriptService(manuscript_repo)

    app.extensions["delete_manuscript_service"] = delete_manuscript_service

    return app
