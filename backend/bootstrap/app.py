# app.py
import logging
import os
from flask import Flask

from .container import Container, build_container
from .extensions import limiter
from domain.identity.api.auth.routes import auth_bp
from domain.project.api.routes import project_bp
from .error_handlers import register_error_handlers


def configure_logging(log_path: str = "logs/app.log") -> None:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    handler = logging.FileHandler(log_path)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logging.root.setLevel(logging.WARNING)
    logging.root.addHandler(handler)


def create_app(
    config: dict | None = None,
    container: Container | None = None,
) -> Flask:
    app = Flask(__name__)
    app.config.update(config or {})

    configure_logging()

    limiter.init_app(app)

    app.extensions["container"] = container or build_container()
    register_error_handlers(app)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(project_bp, url_prefix="/api/projects")

    return app
