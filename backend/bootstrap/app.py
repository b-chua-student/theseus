"""Flask application factory."""

import os
from collections.abc import Mapping
from secrets import token_hex

import click
from dotenv import load_dotenv
from flask import Flask, Response, abort, send_from_directory

from domain.assistant.api.routes import conversation_bp, indexing_bp
from domain.assistant.infrastructure.ports.chat_model import ChatModel
from domain.assistant.infrastructure.ports.embedding_generator import EmbeddingGenerator
from domain.identity.api.auth.routes import auth_bp
from domain.manuscript.api.routes import manuscript_bp
from domain.project.api.routes import project_bp
from domain.revision_history.api.routes import draft_bp, revision_bp
from domain.src_lib.api.routes import source_bp

from .container import Container, build_container, build_mongo_container
from .error_handlers import register_error_handlers
from .extensions import limiter


def _build_chat_model() -> ChatModel | None:
    if not os.getenv("GEMINI_API_KEY"):
        return None

    from domain.assistant.infrastructure.adapters.gemini_chat_model import GeminiChatModel

    return GeminiChatModel()


def _build_embedding_generator() -> EmbeddingGenerator | None:
    """Use semantic Gemini embeddings when a key is set; otherwise keep the in-memory default."""
    if not os.getenv("GEMINI_API_KEY"):
        return None

    from domain.assistant.infrastructure.adapters.gemini_embedding_generator import (
        GeminiEmbeddingGenerator,
    )

    return GeminiEmbeddingGenerator()


def create_app(
    config: Mapping[str, object] | None = None,
    container: Container | None = None,
) -> Flask:
    """Create the Flask application and wire the bounded contexts."""
    load_dotenv()
    app = Flask(__name__, static_folder="../static/assets", static_url_path="/assets")
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY") or None,
        MONGODB_URI=os.getenv("MONGODB_URI"),
        MONGODB_DB=os.getenv("MONGODB_DB"),
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE") == "1",
    )
    app.config.update(config or {})

    if app.testing:
        app.config.setdefault("RATELIMIT_ENABLED", False)

    if container is None:
        chat_model = None if app.testing else _build_chat_model()
        embedding_generator = None if app.testing else _build_embedding_generator()
        if not app.testing and (uri := app.config["MONGODB_URI"]):
            if not app.secret_key:
                raise RuntimeError("Set SECRET_KEY when running with MongoDB.")
            container = build_mongo_container(
                uri=uri,
                db_name=app.config["MONGODB_DB"],
                chat_model=chat_model,
                embedding_generator=embedding_generator,
            )
        else:
            container = build_container(
                chat_model=chat_model, embedding_generator=embedding_generator
            )

    if not app.secret_key:
        app.secret_key = token_hex(32)

    app.extensions["container"] = container
    limiter.init_app(app)
    register_error_handlers(app)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(project_bp, url_prefix="/api/projects")
    manuscripts = "/api/projects/<project_id>/manuscripts"
    app.register_blueprint(manuscript_bp, url_prefix=manuscripts)
    app.register_blueprint(source_bp, url_prefix="/api/sources")
    app.register_blueprint(draft_bp, url_prefix=f"{manuscripts}/<manuscript_id>/drafts")
    app.register_blueprint(revision_bp, url_prefix=f"{manuscripts}/<manuscript_id>/revisions")
    app.register_blueprint(indexing_bp, url_prefix=manuscripts)
    app.register_blueprint(conversation_bp, url_prefix="/api/projects/<project_id>/conversations")

    limiter.exempt(app.send_static_file)

    @app.cli.command("reindex-documents")
    def reindex_documents() -> None:
        """Re-embed every indexed document, for example after changing the embedding model."""
        reindex = app.extensions["container"].assistant.reindex
        if reindex is None:
            raise click.ClickException("Document indexing is not configured.")
        click.echo(f"Re-queued {reindex.execute()} documents for indexing.")

    @app.get("/")
    @limiter.exempt
    def index() -> Response:
        """Serve the built frontend entry point."""
        return send_from_directory("../static", "index.html")

    @app.get("/favicon.svg")
    @limiter.exempt
    def favicon() -> Response:
        """Serve the frontend favicon."""
        return send_from_directory("../static", "favicon.svg")

    @app.get("/api/health")
    @limiter.exempt
    def health() -> dict[str, str]:
        """Report that the application is running."""
        return {"status": "ok"}

    @app.get("/<path:path>")
    @limiter.exempt
    def frontend_fallback(path: str) -> Response:
        """Serve the frontend entry point for client-side routes."""
        if path.partition("/")[0] in {"api", "assets"}:
            abort(404)
        return index()

    return app
