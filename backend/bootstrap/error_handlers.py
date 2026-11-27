import logging
from dataclasses import asdict

from flask import Flask, Response, jsonify
from werkzeug.exceptions import HTTPException

from domain.assistant.models.errors import (
    AnswerValidationError,
    ChatModelError,
    ChatModelRateLimitedError,
    ChatRequestTooLargeError,
    ChatUnavailableError,
    ConversationNotFoundError,
    PendingExchangeError,
)
from domain.identity.services.auth.errors import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    WeakPasswordError,
)
from domain.manuscript.api.errors import ManuscriptNotFoundError
from domain.project.api.errors import ProjectNotFoundError
from domain.revision_history.models.errors import (
    ConcurrentModificationError,
    DraftNotFoundError,
    InvalidResolutionError,
    MergeConflictError,
    MergeInProgressError,
    NoChangesError,
    UnsavedChangesError,
)
from domain.revision_history.services.errors import (
    HistoryNotFound,
    ManuscriptNotFound,
)
from domain.shared.errors import DomainError
from domain.src_lib.api.errors import SourceNotFoundError

logger = logging.getLogger(__name__)


def log_invalid_credentials(error: Exception) -> None:
    """Record an authentication rejection without request or provider data."""
    logger.warning("Invalid credentials attempt: %s", error)


def register_error_handlers(app: Flask) -> None:
    """Register handlers that map domain and service errors to JSON HTTP responses."""

    @app.errorhandler(DraftNotFoundError)
    def handle_draft_not_found(e: DraftNotFoundError) -> tuple[Response, int]:
        return jsonify(error="Draft not found", code=e.code), 404

    @app.errorhandler(NoChangesError)
    @app.errorhandler(UnsavedChangesError)
    @app.errorhandler(MergeInProgressError)
    @app.errorhandler(ConcurrentModificationError)
    def handle_merge_rejected(e: DomainError) -> tuple[Response, int]:
        return jsonify(error=e.message, code=e.code), 409

    @app.errorhandler(MergeConflictError)
    def handle_merge_conflict(e: MergeConflictError) -> tuple[Response, int]:
        return jsonify(
            error=e.message, code=e.code, conflicts=[asdict(c) for c in e.conflicts]
        ), 409

    @app.errorhandler(InvalidResolutionError)
    def handle_invalid_resolution(e: InvalidResolutionError) -> tuple[Response, int]:
        return jsonify(error=e.message, code=e.code, details=e.details), 422

    @app.errorhandler(InvalidCredentialsError)
    def handle_invalid_credentials(e: Exception) -> tuple[Response, int]:
        log_invalid_credentials(e)
        return jsonify(error="Invalid credentials"), 401

    @app.errorhandler(EmailAlreadyRegisteredError)
    def handle_email_taken(e: Exception) -> tuple[Response, int]:
        logger.warning("Email already registered: %s", e)
        return jsonify(error="Email already registered"), 409

    @app.errorhandler(WeakPasswordError)
    def handle_weak_password(e: Exception) -> tuple[Response, int]:
        logger.warning("Weak password: %s", e)
        return jsonify(error="Password does not meet requirements"), 422

    @app.errorhandler(ProjectNotFoundError)
    def handle_project_not_found(e: Exception) -> tuple[Response, int]:
        logger.warning("Project not found: %s", e)
        return jsonify(error="Project not found"), 404

    @app.errorhandler(ManuscriptNotFoundError)
    def handle_manuscript_not_found(e: Exception) -> tuple[Response, int]:
        logger.warning("Manuscript not found: %s", e)
        return jsonify(error="Manuscript not found"), 404

    @app.errorhandler(SourceNotFoundError)
    def handle_source_not_found(e: Exception) -> tuple[Response, int]:
        logger.warning("Source not found: %s", e)
        return jsonify(error="Source not found"), 404

    @app.errorhandler(DomainError)
    def handle_domain_error(e: DomainError) -> tuple[Response, int]:
        logger.warning("Domain error: %s", e)
        # Domain messages are written for users (validation, conflicts), so surface them.
        return jsonify(error=e.message or "Bad request", code=e.code), 400

    @app.errorhandler(ConversationNotFoundError)
    def handle_conversation_not_found(e: ConversationNotFoundError) -> tuple[Response, int]:
        logger.warning("Conversation not found: %s", e)
        return jsonify(error="Conversation not found", code=e.code), 404

    @app.errorhandler(PendingExchangeError)
    def handle_pending_exchange(e: PendingExchangeError) -> tuple[Response, int]:
        logger.warning("Pending exchange: %s", e)
        return jsonify(error="The previous question is still being answered.", code=e.code), 409

    @app.errorhandler(ChatUnavailableError)
    def handle_chat_unavailable(e: ChatUnavailableError) -> tuple[Response, int]:
        logger.warning("Assistant unavailable: %s", e)
        return jsonify(error="The assistant is not available right now.", code=e.code), 503

    @app.errorhandler(ChatModelRateLimitedError)
    def handle_model_rate_limited(e: ChatModelRateLimitedError) -> tuple[Response, int]:
        logger.warning("AI provider rate limited: %s", e)
        response = jsonify(
            error="The assistant is busy. Please try again in a moment.", code=e.code
        )
        response.headers["Retry-After"] = "30"
        return response, 429

    @app.errorhandler(AnswerValidationError)
    def handle_validation_interrupted(e: AnswerValidationError) -> tuple[Response, int]:
        logger.warning("Answer validation interrupted: %s", e)
        return jsonify(error=str(e), code=e.code), 502

    @app.errorhandler(ChatRequestTooLargeError)
    def handle_request_too_large(e: ChatRequestTooLargeError) -> tuple[Response, int]:
        logger.warning("Assistant request too large: %s", e)
        return jsonify(
            error="The selected context is too large for the assistant. "
            "Uncheck some sources or quote a shorter passage, then try again.",
            code=e.code,
        ), 413

    @app.errorhandler(ChatModelError)
    def handle_model_error(e: ChatModelError) -> tuple[Response, int]:
        logger.warning("AI provider failure: %s", e)
        return jsonify(
            error="The assistant couldn't answer right now. Please try again.", code=e.code
        ), 502

    @app.errorhandler(HTTPException)
    def handle_http_error(e: HTTPException) -> tuple[Response, int]:
        return jsonify(error=e.description), e.code or 500

    @app.errorhandler(Exception)
    def handle_unexpected(e: Exception) -> tuple[Response, int]:
        logger.exception("Unhandled error: %s", e)
        return jsonify(error="Internal server error"), 500

    @app.errorhandler(HistoryNotFound)
    @app.errorhandler(ManuscriptNotFound)  # from revision_history.services.errors
    def handle_history_not_found(e: Exception) -> tuple[Response, int]:
        return jsonify(error="Not found"), 404
