# app.py
import logging
import os

from flask import Flask, abort, jsonify, send_from_directory
from flask.typing import ResponseReturnValue

from domain.assistant.api.routes import conversation_bp, indexing_bp
from domain.assistant.infrastructure.ports.chat_model import ChatModel
from domain.identity.api.auth.routes import auth_bp
from domain.manuscript.api.routes import manuscript_bp
from domain.project.api.routes import project_bp
from domain.revision_history.api.routes import draft_bp, revision_bp
from domain.src_lib.api.routes import source_bp

from .container import Container, build_container, build_mongo_container
from .error_handlers import register_error_handlers
from .extensions import limiter


def configure_logging(log_path: str | None = "logs/app.log") -> None:
    """Log to stdout in production (log_path=None), to a file otherwise.

    Hosts like Render capture stdout/stderr directly and expect processes not to
    rely on a writable local disk for anything that matters, so the file handler
    used for local development is skipped there.
    """
    handler = logging.FileHandler(log_path) if log_path else logging.StreamHandler()
    if log_path:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logging.root.setLevel(logging.WARNING)
    logging.root.addHandler(handler)


def _build_default_chat_model() -> ChatModel | None:
    """Construct the Gemini chat model when its SDK and API key are available.

    Returns ``None`` when the dependency or ``GEMINI_API_KEY`` is missing, so the
    container can still be built without a chat provider (e.g. in tests).
    """
    try:
        from domain.assistant.infrastructure.adapters.gemini_chat_model import GeminiChatModel

        return GeminiChatModel()
    except (ImportError, ValueError):
        return None


def create_app(
    config: dict | None = None,
    container: Container | None = None,
) -> Flask:
    """Create and configure the Flask application, wiring the container, blueprints and handlers."""
    app = Flask(__name__)
    app.config.update(config or {})

    configure_logging(None if os.getenv("LOG_TO_STDOUT") == "1" else "logs/app.log")

    limiter.init_app(app)

    if container is None:
        if (config or {}).get("TESTING"):
            # Tests get a fully in-memory container: they never construct the Gemini
            # client (the suite stays hermetic) and never touch the real database.
            container = build_container()
        else:
            container = build_mongo_container(chat_model=_build_default_chat_model())
    app.extensions["container"] = container
    register_error_handlers(app)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(project_bp, url_prefix="/api/projects")
    app.register_blueprint(manuscript_bp, url_prefix="/api/projects/<project_id>/manuscripts")
    app.register_blueprint(source_bp, url_prefix="/api/sources")
    app.register_blueprint(
        draft_bp, url_prefix="/api/projects/<project_id>/manuscripts/<manuscript_id>/drafts"
    )
    app.register_blueprint(
        revision_bp, url_prefix="/api/projects/<project_id>/manuscripts/<manuscript_id>/revisions"
    )
    app.register_blueprint(indexing_bp, url_prefix="/api/projects/<project_id>/manuscripts")
    app.register_blueprint(conversation_bp, url_prefix="/api/projects/<project_id>/conversations")

    _register_health_check(app)
    if frontend_dist := os.getenv("FRONTEND_DIST"):
        _register_frontend(app, frontend_dist)

    return app


def _register_health_check(app: Flask) -> None:
    # Exempt from rate limiting: a platform health checker hits this constantly and
    # must never be answered with 429, which would get the service restarted.
    @app.get("/healthz")
    @limiter.exempt
    def healthz() -> ResponseReturnValue:
        return jsonify(status="ok"), 200


def _register_frontend(app: Flask, dist_dir: str) -> None:
    """Serve the built single-page app from the same origin as the API.

    One origin means the browser's session cookie "just works" and no CORS setup is
    needed. Unknown non-API paths fall back to index.html so client-side routes load.
    """
    root = os.path.abspath(dist_dir)

    # Static files are exempt from rate limiting: one page load fetches many assets,
    # and counting them would burn the per-IP budget meant for API calls.
    @app.get("/", defaults={"path": ""})
    @app.get("/<path:path>")
    @limiter.exempt
    def frontend(path: str) -> ResponseReturnValue:
        if path == "api" or path.startswith("api/"):
            abort(404)
        if path and os.path.isfile(os.path.join(root, path)):
            # Vite fingerprints everything under assets/, so it can be cached forever.
            max_age = 31536000 if path.startswith("assets/") else 0
            return send_from_directory(root, path, max_age=max_age)
        return send_from_directory(root, "index.html", max_age=0)
