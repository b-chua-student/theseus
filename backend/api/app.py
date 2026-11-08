"""Flask application factory."""

from flask import Flask


def create_app() -> Flask:
    """Create and configure the Flask application.

    Returns:
        A configured Flask application instance.
    """
    app = Flask(__name__)
    return app
