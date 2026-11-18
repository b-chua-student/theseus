"""Flask application factory."""

from flask import Flask, Response, abort, send_from_directory


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

    @app.get("/<path:path>")
    def frontend_fallback(path: str) -> Response:
        """Serve the frontend entry point for client-side routes."""
        if path.partition("/")[0] in {"api", "assets"}:
            abort(404)
        return index()

    return app
