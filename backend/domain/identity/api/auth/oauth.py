import base64
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
from datetime import UTC, datetime
from urllib.parse import urlencode

import jwt
import requests
from flask import Blueprint, Flask, current_app, jsonify, redirect, request, session
from flask.typing import ResponseReturnValue

from bootstrap.error_handlers import log_invalid_credentials
from domain.identity.infrastructure.ports.identity_repository import (
    IdentityConflict,
    IdentityRepository,
)
from domain.identity.models.aggregates import User
from domain.identity.models.errors import InvalidDisplayNameError, InvalidEmailError
from domain.identity.models.value_objects import DisplayName, Email, UserId
from domain.identity.services.auth.errors import InvalidCredentialsError
from domain.identity.services.auth.pending import PendingAttempts, PostgresPendingAttempts

from .routes import establish_session, login_required

oauth = Blueprint("oauth", __name__)


class CallbackLogFilter(logging.Filter):
    """Omit query strings from callback URLs in development and deployment access logs."""

    callback_query = re.compile(r"(/api/auth/oauth/[^/\s?]+/callback)\?[^\s\"\x1b]+")

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact callback query parameters before handlers format the record."""
        message = record.getMessage()
        if "/callback?" in message:
            record.msg = self.callback_query.sub(r"\1", message)
            record.args = ()
        return True


access_filter = CallbackLogFilter()


def configure(app: Flask, repo: IdentityRepository) -> None:
    """Register provider endpoints and select the pending-request store."""
    for logger_name in ("werkzeug", "gunicorn.access"):
        logging.getLogger(logger_name).addFilter(access_filter)
    # Mongo deployments share attempts across workers. The development container is in-memory.
    collection = repo.users.database["oauth_attempts"] if hasattr(repo, "users") else None
    app.extensions["oauth_attempts"] = (
        PostgresPendingAttempts(repo.conn) if hasattr(repo, "conn") else PendingAttempts(collection)
    )
    configured = app.config.setdefault(
        "OAUTH_PROVIDERS", json.loads(os.getenv("OAUTH_PROVIDERS", "{}"))
    )
    app.config["OAUTH_PROVIDERS"] = (
        {"google": configured["google"]} if "google" in configured else {}
    )
    if app.config["OAUTH_PROVIDERS"] and not app.testing:
        app.config["SESSION_COOKIE_SECURE"] = True
    app.register_blueprint(oauth, url_prefix="/api/auth")


def repository() -> IdentityRepository:
    """Return the configured identity repository."""
    return current_app.extensions["container"].identity.repository


def failure(code: str, provider: str) -> ResponseReturnValue:
    """Record the ordinary rejection and redirect with a public error code."""
    log_invalid_credentials(InvalidCredentialsError())
    return redirect("/?" + urlencode({"auth_error": code, "provider": provider}))


@oauth.get("/oauth/providers")
def providers() -> ResponseReturnValue:
    """Return configured providers and recovery state for this browser."""
    response = jsonify(
        providers=list(current_app.config["OAUTH_PROVIDERS"]),
        interrupted=bool(session.get("oauth_attempt")),
        csrf=session.get("oauth_csrf"),
    )

    response.cache_control.no_store = True
    return response


def begin(provider: str, *, link: bool = False) -> ResponseReturnValue:
    """Bind one authorization attempt to this session."""
    config = current_app.config["OAUTH_PROVIDERS"].get(provider)
    if config is None:
        return jsonify(error="Unknown provider"), 404
    store = current_app.extensions["oauth_attempts"]
    store.take(session.pop("oauth_attempt", None))
    return_to = request.args.get("return_to")
    verifier = secrets.token_urlsafe(64)
    attempt = dict(
        provider=provider,
        state=secrets.token_urlsafe(32),
        nonce=secrets.token_urlsafe(32),
        verifier=verifier,
        account=session.get("user_id") if link else None,
        destination=return_to if return_to in {"/workspace", "/projects"} else "/",
    )
    session["oauth_attempt"] = store.put(attempt)
    digest = hashlib.sha256(verifier.encode()).digest()
    params = dict(
        response_type="code",
        client_id=config["client_id"],
        redirect_uri=config["redirect_uri"],
        scope="openid email profile",
        state=attempt["state"],
        nonce=attempt["nonce"],
        code_challenge_method="S256",
        code_challenge=base64.urlsafe_b64encode(digest).rstrip(b"=").decode(),
    )
    destination = config["authorization_endpoint"] + "?" + urlencode(params)
    return jsonify(location=destination) if link else redirect(destination)


@oauth.get("/oauth/<provider>/start")
def start(provider: str) -> ResponseReturnValue:
    """Redirect to the selected provider for sign-in."""
    return begin(provider)


def csrf_valid() -> bool:
    """Verify the session token for an authenticated account action."""
    expected = session.get("oauth_csrf")
    return bool(
        expected
        and secrets.compare_digest(
            expected.encode(), request.headers.get("X-CSRF-Token", "").encode()
        )
    )


@oauth.post("/oauth/<provider>/link")
@login_required
def link(provider: str) -> ResponseReturnValue:
    """Start explicit linking from an authenticated session."""
    if not csrf_valid():
        return jsonify(error="Invalid request"), 403
    return begin(provider, link=True)


@oauth.patch("/me")
@login_required
def update_profile() -> ResponseReturnValue:
    """Validate and save the signed-in user’s display name."""
    if not csrf_valid():
        return jsonify(error="Invalid request"), 403
    try:
        name = DisplayName((request.get_json() or {}).get("display_name", "")).value
    except (InvalidDisplayNameError, AttributeError):
        return jsonify(error="Enter a name between 1 and 50 characters."), 400
    user = repository().get_by_id(UserId.from_str(session["user_id"]))
    if not user:
        return jsonify(error="Unauthorized"), 401
    repository().rename(user, name)
    return jsonify(display_name=name)


def validated_claims(config: dict, attempt: dict, code: str) -> dict:
    """Redeem the code and extract allowlisted claims from the validated ID token."""
    response = requests.post(
        config["token_endpoint"],
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": config["redirect_uri"],
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "code_verifier": attempt["verifier"],
        },
        timeout=(8, 20),
        allow_redirects=False,
    )
    response.raise_for_status()
    token = response.json()["id_token"]
    key = jwt.PyJWKClient(config["jwks_uri"], timeout=8).get_signing_key_from_jwt(token)
    claims = jwt.decode(
        token,
        key.key,
        algorithms=["RS256"],
        audience=config["client_id"],
        issuer=config["issuer"],
        leeway=60,
        options={"require": ["sub", "exp", "iat", "nonce"]},
    )
    # PyJWT also applies leeway to expiry. Only allow skew on the start of validity.
    if int(claims["exp"]) <= datetime.now(UTC).timestamp():
        raise jwt.ExpiredSignatureError("Provider token has expired")
    if claims["nonce"] != attempt["nonce"] or not claims["sub"]:
        raise ValueError("Invalid identity")
    if isinstance(claims["aud"], list) and len(claims["aud"]) > 1 and "azp" not in claims:
        raise ValueError("Missing authorized party")
    if claims.get("azp", config["client_id"]) != config["client_id"]:
        raise ValueError("Invalid authorized party")
    return {key: claims.get(key) for key in ("iss", "sub", "name", "email", "email_verified")}


@oauth.get("/oauth/<provider>/callback")
def callback(provider: str) -> ResponseReturnValue:
    """Consume the attempt and validate the provider response."""
    attempt = current_app.extensions["oauth_attempts"].take(session.pop("oauth_attempt", None))
    if (
        not attempt
        or attempt["provider"] != provider
        or not hmac.compare_digest(
            attempt["state"].encode(), request.args.get("state", "").encode()
        )
    ):
        current_app.logger.warning("OAuth callback rejected: missing attempt or state mismatch")
        return failure("invalid", provider)
    expires = attempt["expires"]
    if expires.tzinfo is None:  # MongoDB returns naive UTC by default.
        expires = expires.replace(tzinfo=UTC)
    if expires <= datetime.now(UTC):
        current_app.logger.warning("OAuth callback rejected: authorization attempt expired")
        return failure("timeout", provider)
    if attempt["account"] != session.get("user_id"):
        return failure("invalid", provider)
    error = request.args.get("error")
    if error:
        return failure("cancelled" if error == "access_denied" else "provider", provider)
    config = current_app.config["OAUTH_PROVIDERS"].get(provider)
    if not config or not request.args.get("code"):
        return failure("invalid", provider)
    try:
        claims = validated_claims(config, attempt, request.args["code"])
    except requests.Timeout:
        current_app.logger.warning("OAuth token endpoint timed out")
        return failure("timeout", provider)
    except requests.HTTPError as exc:
        reason = "token request rejected"
        if exc.response is not None:
            try:
                payload = exc.response.json()
                code = payload.get("error") if isinstance(payload, dict) else None
                if code in ("invalid_client", "invalid_grant", "unauthorized_client"):
                    reason = code
            except ValueError:
                pass
        current_app.logger.warning("OAuth token exchange: %s", reason)
        return failure("invalid", provider)
    except (requests.RequestException, jwt.PyJWTError, KeyError, ValueError, TypeError) as exc:
        current_app.logger.warning("OAuth provider validation failed: %s", type(exc).__name__)
        return failure("invalid", provider)
    try:
        return finish(attempt, claims, provider)
    except Exception:
        # Driver errors can contain values from the attempted write.
        current_app.logger.error("Could not complete identity storage operation")
        return failure("invalid", provider)


def finish(attempt: dict, claims: dict, provider: str) -> ResponseReturnValue:
    """Resolve the validated subject and commit the appropriate account action."""
    try:
        email = Email(claims.get("email") or "")
    except (InvalidEmailError, TypeError, AttributeError):
        return failure("email", provider)
    repo = repository()
    pair = (claims["iss"], claims["sub"])
    user = repo.find_identity(*pair)
    if attempt["account"]:
        account = repo.get_by_id(UserId.from_str(attempt["account"]))
        if not account or account.status == "suspended":
            return failure("unavailable", provider)
        try:
            repo.link(account, *pair)
        except IdentityConflict:
            return failure("existing", provider)
        return redirect("/")
    if user is None:
        raw_name = claims.get("name")
        name = raw_name.strip() if isinstance(raw_name, str) else ""
        candidate = User(
            UserId.new(),
            DisplayName(name if 1 <= len(name) <= 50 else "Theseus user"),
            email,
            None,
            verified=claims.get("email_verified") is True,
        )
        try:
            repo.provision(candidate, *pair)
            user = candidate
        except IdentityConflict:
            user = repo.find_identity(*pair)
            if user is None:
                return failure("existing" if repo.get_by_email(email) else "invalid", provider)
    if user.status == "suspended":
        return failure("unavailable", provider)
    establish_session(str(user.id.value))
    return redirect(attempt["destination"])
