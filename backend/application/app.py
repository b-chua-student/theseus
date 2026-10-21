from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

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

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/day", "20/hour"],
    storage_uri="memory://",
)


def create_app() -> Flask:
    app = Flask(__name__)

    app.register_blueprint(manuscripts_bp, url_prefix="/api/manuscripts")

    manuscript_repository = FakeManuscriptRepository(seed=True)
    revision_history_repository = FakeRevisionHistoryRepository()

    create_manuscript_service = CreateManuscriptService(
        manuscript_repo=manuscript_repository, revision_history_repo=revision_history_repository
    )

    app.extensions["create_manuscript_service"] = create_manuscript_service

    get_all_manuscripts_service = GetAllManuscriptService(repository=manuscript_repository)

    app.extensions["get_all_manuscripts_service"] = get_all_manuscripts_service

    get_manuscript_service = GetManuscriptService(repository=manuscript_repository)

    app.extensions["get_manuscript_service"] = get_manuscript_service

    delete_manuscript_service = DeleteManuscriptService(manuscript_repository)

    app.extensions["delete_manuscript_service"] = delete_manuscript_service

    return app
