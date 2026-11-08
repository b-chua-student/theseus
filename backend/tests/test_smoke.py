"""Smoke tests for the application factory."""

from api.app import create_app


def test_create_app() -> None:
    """Verify create_app produces a usable Flask application."""
    create_app()
