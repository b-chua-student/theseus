"""Flask application factory."""

from flask import Flask, Response, send_from_directory


def create_app() -> Flask:
    """Create and configure the Flask application.

    Returns:
        A configured Flask application instance.
    """
    app = Flask(__name__, static_folder="../static/assets", static_url_path="/assets")

    @app.get("/")
    def index() -> Response:
        """Serve the built frontend entry point."""
        return send_from_directory("../static", "index.html")

    @app.get("/favicon.svg")
    def favicon() -> Response:
        """Serve the frontend favicon."""
        return send_from_directory("../static", "favicon.svg")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        """Report that the application is running."""
        return {"status": "ok"}

    return app
