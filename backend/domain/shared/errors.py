from __future__ import annotations

from typing import Any


class DomainError(Exception):
    """Base class for domain errors, carrying a message, code and details."""

    code: str = "domain.error"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ServiceError(Exception):
    """Base class for application service errors."""

    pass
