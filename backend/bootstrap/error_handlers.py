import logging

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from domain.identity.services.auth.errors import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    WeakPasswordError,
)
from domain.identity.models.errors import DomainError
from domain.project.api.errors import ProjectNotFoundError

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(InvalidCredentialsError)
    def handle_invalid_credentials(e):
        logger.warning("Invalid credentials attempt: %s", e)
        return jsonify(error="Invalid credentials"), 401

    @app.errorhandler(EmailAlreadyRegisteredError)
    def handle_email_taken(e):
        logger.warning("Email already registered: %s", e)
        return jsonify(error="Email already registered"), 409

    @app.errorhandler(WeakPasswordError)
    def handle_weak_password(e):
        logger.warning("Weak password: %s", e)
        return jsonify(error="Password does not meet requirements"), 422

    @app.errorhandler(ProjectNotFoundError)
    def handle_project_not_found(e):
        logger.warning("Project not found: %s", e)
        return jsonify(error="Project not found"), 404

    @app.errorhandler(DomainError)
    def handle_domain_error(e):
        logger.warning("Domain error: %s", e)
        return jsonify(error="Bad request"), 400

    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        return jsonify(error=e.description), e.code

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        logger.exception("Unhandled error: %s", e)
        return jsonify(error="Internal server error"), 500
