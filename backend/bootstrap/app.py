"""Flask application factory."""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from secrets import token_hex

import click
from dotenv import load_dotenv
from flask import Flask, Response, abort, send_from_directory

from domain.assistant.api.routes import conversation_bp, indexing_bp, library_bp
from domain.assistant.infrastructure.ports.answer_validator import AnswerValidator
from domain.assistant.infrastructure.ports.chat_model import ChatModel
from domain.assistant.infrastructure.ports.embedding_generator import EmbeddingGenerator
from domain.assistant.infrastructure.ports.token_counter import TokenCounter
from domain.identity.api.auth.oauth import configure as configure_oauth
from domain.identity.api.auth.routes import auth_bp
from domain.manuscript.api.routes import manuscript_bp
from domain.project.api.routes import project_bp
from domain.revision_history.api.routes import draft_bp, revision_bp
from domain.src_lib.api.routes import source_bp

from .container import Container, build_container, build_mongo_container
from .error_handlers import register_error_handlers
from .extensions import limiter


def _build_embedding_generator() -> EmbeddingGenerator | None:
    """Use semantic Gemini embeddings when a key is set; otherwise keep the in-memory default."""
    if not os.getenv("GEMINI_API_KEY"):
        return None

    from domain.assistant.infrastructure.adapters.gemini_embedding_generator import (
        GeminiEmbeddingGenerator,
    )

    return GeminiEmbeddingGenerator()


# The model's input window and the tokens kept free for its answer. Override with
# ASSISTANT_CONTEXT_WINDOW and ASSISTANT_RESPONSE_RESERVE.
DEFAULT_CONTEXT_WINDOW = 1_048_576
DEFAULT_RESPONSE_RESERVE = 16_384


@dataclass(frozen=True)
class _EvidenceSettings:
    """How the assistant picks library evidence for each exchange."""

    relevance_threshold: float | None = None
    token_counter: TokenCounter | None = None
    context_window: int | None = None
    response_reserve: int = 0
    gemini_chat_model: str | None = None


def _build_evidence_settings() -> _EvidenceSettings:
    """Read the evidence settings from the environment.

    ASSISTANT_RELEVANCE_THRESHOLD is the lowest cosine score a passage may have. It is not
    set by default: calibrate it with the semantic embedding model before enabling it. With a
    Gemini key, evidence is also fitted into the model's window using Gemini token counts.
    """
    threshold = os.getenv("ASSISTANT_RELEVANCE_THRESHOLD")
    relevance_threshold = float(threshold) if threshold else None
    if not os.getenv("GEMINI_API_KEY"):
        return _EvidenceSettings(relevance_threshold=relevance_threshold)

    from domain.assistant.infrastructure.adapters.gemini_chat_model import DEFAULT_MODEL
    from domain.assistant.infrastructure.adapters.gemini_token_counter import GeminiTokenCounter

    model = (os.getenv("GEMINI_CHAT_MODEL") or "").strip() or DEFAULT_MODEL
    return _EvidenceSettings(
        relevance_threshold=relevance_threshold,
        token_counter=GeminiTokenCounter(model=model),
        context_window=int(os.getenv("ASSISTANT_CONTEXT_WINDOW") or DEFAULT_CONTEXT_WINDOW),
        response_reserve=int(os.getenv("ASSISTANT_RESPONSE_RESERVE") or DEFAULT_RESPONSE_RESERVE),
        gemini_chat_model=model,
    )


def _build_chat_model(evidence: _EvidenceSettings) -> ChatModel | None:
    """Use Gemini when a key is set. It counts each request against the same context window."""
    if evidence.gemini_chat_model is None:
        return None

    from domain.assistant.infrastructure.adapters.gemini_chat_model import GeminiChatModel

    return GeminiChatModel(
        model=evidence.gemini_chat_model,
        token_counter=evidence.token_counter,
        context_window=evidence.context_window,
    )


def _build_answer_validator(evidence: _EvidenceSettings) -> AnswerValidator | None:
    if evidence.gemini_chat_model is None:
        return None

    from domain.assistant.infrastructure.adapters.gemini_answer_validator import (
        GeminiAnswerValidator,
    )

    return GeminiAnswerValidator(model=evidence.gemini_chat_model)


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
        embedding_generator = None if app.testing else _build_embedding_generator()
        evidence = _EvidenceSettings() if app.testing else _build_evidence_settings()
        chat_model = None if app.testing else _build_chat_model(evidence)
        answer_validator = None if app.testing else _build_answer_validator(evidence)
        if not app.testing and (uri := app.config["MONGODB_URI"]):
            if not app.secret_key:
                raise RuntimeError("Set SECRET_KEY when running with MongoDB.")
            container = build_mongo_container(
                uri=uri,
                db_name=app.config["MONGODB_DB"],
                answer_validator=answer_validator,
                chat_model=chat_model,
                embedding_generator=embedding_generator,
                relevance_threshold=evidence.relevance_threshold,
                token_counter=evidence.token_counter,
                context_window=evidence.context_window,
                response_reserve=evidence.response_reserve,
            )
        else:
            container = build_container(
                chat_model=chat_model,
                answer_validator=answer_validator,
                embedding_generator=embedding_generator,
                relevance_threshold=evidence.relevance_threshold,
                token_counter=evidence.token_counter,
                context_window=evidence.context_window,
                response_reserve=evidence.response_reserve,
            )

    if not app.secret_key:
        app.secret_key = token_hex(32)

    app.extensions["container"] = container
    configure_oauth(app, container.identity.repository)
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
    app.register_blueprint(library_bp, url_prefix="/api/projects/<project_id>")

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
