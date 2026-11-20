"""Pytest configuration and local fallback stubs for cross-domain dependencies."""

from __future__ import annotations

import importlib
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from functools import wraps
from types import ModuleType
from typing import ParamSpec, TypeVar

from flask import jsonify, session
from flask.typing import ResponseReturnValue

P = ParamSpec("P")
R = TypeVar("R")


def _ensure_shared_modules() -> None:
    """Provide fallback domain.shared modules if not present on the local branch."""
    try:
        importlib.import_module("domain.shared.clock")
        importlib.import_module("domain.shared.errors")
    except ModuleNotFoundError:
        shared_pkg = sys.modules.setdefault("domain.shared", ModuleType("domain.shared"))
        shared_pkg.__path__ = []

        clock_mod = ModuleType("domain.shared.clock")
        clock_mod.now = lambda: datetime.now(UTC)  # type: ignore[attr-defined]
        sys.modules["domain.shared.clock"] = clock_mod

        errors_mod = ModuleType("domain.shared.errors")

        class DomainError(Exception):
            """Fallback base domain error."""

        errors_mod.DomainError = DomainError  # type: ignore[attr-defined]
        sys.modules["domain.shared.errors"] = errors_mod


def _ensure_identity_modules() -> None:
    """Provide a fallback login_required decorator if domain.identity is absent locally."""
    try:
        importlib.import_module("domain.identity.api.auth.routes")
    except ModuleNotFoundError:
        for pkg_name in (
            "domain.identity",
            "domain.identity.api",
            "domain.identity.api.auth",
        ):
            pkg = sys.modules.setdefault(pkg_name, ModuleType(pkg_name))
            pkg.__path__ = []

        routes_mod = ModuleType("domain.identity.api.auth.routes")

        def login_required(fn: Callable[P, R]) -> Callable[P, R | ResponseReturnValue]:
            @wraps(fn)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | ResponseReturnValue:
                if "user_id" not in session:
                    return jsonify(error="Unauthorized"), 401
                return fn(*args, **kwargs)

            return wrapper

        routes_mod.login_required = login_required  # type: ignore[attr-defined]
        sys.modules["domain.identity.api.auth.routes"] = routes_mod


_ensure_shared_modules()
_ensure_identity_modules()
