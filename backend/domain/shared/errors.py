from __future__ import annotations
from typing import Any


class DomainError(Exception):
    code: str = "domain.error"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ServiceError(Exception):
    pass
