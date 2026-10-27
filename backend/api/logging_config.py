"""Logging configuration for the Theseus backend.

Sets up a consistent log format, honours the ``LOG_LEVEL`` and ``LOG_FILE``
environment variables, and attaches handlers to the root logger so that every
module can simply call ``logging.getLogger(__name__)``.

Usage (automatic — called inside ``create_app``)::

    from api.logging_config import configure_logging
    configure_logging(app)

Then in any module::

    import logging

    logger = logging.getLogger(__name__)
    logger.info("Something happened")
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys

from flask import Flask

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


def _resolve_level(raw: str) -> int:
    """Convert a level name string to a ``logging`` integer level.

    Falls back to ``INFO`` for unrecognised values.

    Args:
        raw: Level name, e.g. ``"DEBUG"`` or ``"WARNING"``.

    Returns:
        The corresponding :mod:`logging` level integer.
    """
    level = getattr(logging, raw.upper(), None)
    if not isinstance(level, int):
        logging.getLogger(__name__).warning("Unknown LOG_LEVEL %r — defaulting to INFO.", raw)
        return logging.INFO
    return level


def configure_logging(app: Flask) -> None:
    """Configure logging for the Flask application.

    Reads two optional environment variables:

    * ``LOG_LEVEL`` — one of ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``,
      ``CRITICAL``.  Defaults to ``DEBUG`` when Flask's debug mode is active,
      otherwise ``INFO``.
    * ``LOG_FILE`` — if set, a :class:`~logging.handlers.RotatingFileHandler`
      writing to this path is added alongside the stream handler (max 10 MB,
      five backups).

    The Flask app logger is also set to the same level and its default
    handlers are replaced so formatting stays consistent.

    Args:
        app: The Flask application instance.
    """
    raw_level = os.environ.get("LOG_LEVEL", "DEBUG" if app.debug else "INFO")
    level = _resolve_level(raw_level)

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # Stream handler — always present (stdout so Docker / systemd pick it up).
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    handlers: list[logging.Handler] = [stream_handler]

    # Optional rotating file handler.
    log_file = os.environ.get("LOG_FILE", "")
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    # Configure the root logger.
    root = logging.getLogger()
    root.setLevel(level)
    # Remove any handlers already attached (e.g. by a previous create_app call
    # in tests) to avoid duplicate log lines.
    root.handlers.clear()
    for h in handlers:
        root.addHandler(h)

    # Keep Flask's own logger in sync with the root configuration.
    app.logger.handlers.clear()
    app.logger.propagate = True
    app.logger.setLevel(level)

    app.logger.info(
        "Logging configured — level=%s%s",
        logging.getLevelName(level),
        f", file={log_file}" if log_file else "",
    )
