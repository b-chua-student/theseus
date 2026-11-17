"""Flask application factory."""

from flask import Flask


def create_app() -> Flask:
    """Create and configure the Flask application.

    Returns:
        A configured Flask application instance.
    """
    app = Flask(__name__)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        """Report that the application is running."""
        return {"status": "ok"}

    return app
