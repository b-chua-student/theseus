"""Smoke tests for the application factory."""

from api.app import create_app


def test_create_app() -> None:
    """Verify create_app produces a usable Flask application."""
    create_app()


def test_health() -> None:
    """Verify the health endpoint responds successfully over HTTP."""
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == {"status": "ok"}
