from collections.abc import Callable
from functools import wraps

from flask import Blueprint, current_app, jsonify, request, session
from flask.typing import ResponseReturnValue
from pydantic import ValidationError

from bootstrap.extensions import limiter

from .requests import LoginRequest, RegisterRequest

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/login")
@limiter.limit("5 per minute")
def login() -> ResponseReturnValue:
    """Handle POST /login: authenticate the user and start a session (200)."""
    try:
        body = LoginRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError:
        return jsonify(error="Invalid request"), 400

    container = current_app.extensions["container"]

    user = container.identity.auth.login.execute(
        email=body.email,
        password=body.password,
    )

    session.clear()
    session["user_id"] = str(user.id.value)

    return jsonify(id=str(user.id.value), display_name=user.display_name.value), 200


@auth_bp.post("/register")
@limiter.limit("5 per minute")
def register() -> ResponseReturnValue:
    """Handle POST /register: create an account and start a session (201)."""
    try:
        body = RegisterRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError:
        return jsonify(error="Invalid request"), 400

    container = current_app.extensions["container"]

    user = container.identity.auth.register.execute(
        display_name=body.display_name,
        email=body.email,
        password=body.password,
    )

    session.clear()
    session["user_id"] = str(user.id.value)

    return jsonify(id=str(user.id.value), display_name=user.display_name.value), 201


def login_required(view: Callable[..., ResponseReturnValue]) -> Callable[..., ResponseReturnValue]:
    """Wrap a view so it responds 401 unless a user is signed in."""

    @wraps(view)
    def wrapper(*args: object, **kwargs: object) -> ResponseReturnValue:
        if "user_id" not in session:
            return jsonify(error="Unauthorized"), 401
        return view(*args, **kwargs)

    return wrapper


@auth_bp.get("/me")
@login_required
def me() -> ResponseReturnValue:
    """Handle GET /me: return the signed-in user's id, display name and email."""
    container = current_app.extensions["container"]
    user = container.identity.account.get_account.execute(user_id=session["user_id"])
    return jsonify(
        id=str(user.id.value),
        display_name=user.display_name.value,
        email=user.email.value,
    ), 200


@auth_bp.post("/logout")
def logout() -> ResponseReturnValue:
    """Handle POST /logout: clear the session and return 204."""
    session.clear()
    return "", 204
