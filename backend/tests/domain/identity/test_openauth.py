import base64
import hashlib
import json
from collections.abc import Callable
from urllib.parse import parse_qs, urlsplit

import pytest
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from bootstrap.app import create_app


@pytest.fixture
def client() -> FlaskClient:
    provider = {
        "issuer": "https://provider.example",
        "authorization_endpoint": "https://provider.example/authorize",
        "token_endpoint": "https://provider.example/token",
        "jwks_uri": "https://provider.example/keys",
        "client_id": "theseus",
        "client_secret": "secret",
        "redirect_uri": "https://theseus.example/api/auth/oauth/google/callback",
    }
    microsoft = dict(
        provider, redirect_uri="https://theseus.example/api/auth/oauth/microsoft/callback"
    )
    app = create_app(
        {"TESTING": True, "OAUTH_PROVIDERS": {"google": provider, "microsoft": microsoft}}
    )
    return app.test_client()


def start(client, provider_id="google") -> dict[str, str]:
    response = client.get(f"/api/auth/oauth/{provider_id}/start")
    assert response.status_code == 302
    return {k: v[0] for k, v in parse_qs(urlsplit(response.location).query).items()}


def test_s002_authorization(client) -> None:
    first, second = start(client), start(client)
    assert first["response_type"] == "code"
    assert set(first["scope"].split()) == {"openid", "email", "profile"}
    assert first["code_challenge_method"] == "S256"
    for field in ("nonce", "state", "code_challenge"):
        assert first[field] and first[field] != second[field]


@pytest.mark.parametrize(
    ("error", "outcome"),
    [
        ("access_denied", "cancelled"),
        ("server_error", "provider"),
    ],
)
def test_s014_s015_provider_failure(client, error, outcome) -> None:
    params = start(client)
    response = client.get(
        "/api/auth/oauth/google/callback", query_string={"state": params["state"], "error": error}
    )
    assert response.status_code == 302
    assert outcome in response.location
    assert client.get("/api/auth/me").status_code == 401


def test_s019_state_is_single_use(client) -> None:
    params = start(client)
    for state in ("incorrect", params["state"]):
        result = client.get(
            "/api/auth/oauth/google/callback", query_string={"state": state, "code": "unused"}
        )
        assert result.status_code == 302
        assert "invalid" in result.location
        assert client.get("/api/auth/me").status_code == 401


@pytest.fixture
def provider(client, monkeypatch) -> tuple[dict, Callable[..., TestResponse]]:
    import time

    import jwt
    import requests
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    claims = {
        "sub": "reader",
        "email": "reader@example.com",
        "name": "New User",
        "email_verified": False,
    }

    def authorize(
        *, bad_signature=False, code_status="fresh", link=False, provider_id="google"
    ) -> TestResponse:
        if link:
            csrf = client.get("/api/auth/oauth/providers").json["csrf"]
            result = client.post("/api/auth/oauth/google/link", headers={"X-CSRF-Token": csrf})
            params = {k: v[0] for k, v in parse_qs(urlsplit(result.json["location"]).query).items()}
        else:
            params = start(client, provider_id)

        valid_codes = {"approved": time.time() + 60}
        if code_status == "expired":
            valid_codes["approved"] = time.time() - 1
        elif code_status == "redeemed":
            valid_codes.pop("approved")

        def exchange(url, *, data, **kwargs: object) -> requests.Response:
            verifier = data["code_verifier"].encode()
            challenge = (
                base64.urlsafe_b64encode(hashlib.sha256(verifier).digest()).decode().rstrip("=")
            )
            assert challenge == params["code_challenge"]
            assert data["code"] == "approved"
            if valid_codes.pop(data["code"], 0) <= time.time():
                raise requests.HTTPError("invalid_grant")
            payload = {
                "iss": "https://provider.example",
                "aud": "theseus",
                "iat": int(time.time()),
                "exp": int(time.time()) + 120,
                "nonce": params["nonce"],
                **claims,
            }
            signer = (
                rsa.generate_private_key(public_exponent=65537, key_size=2048)
                if bad_signature
                else key
            )
            token = jwt.encode(payload, signer, algorithm="RS256", headers={"kid": "test"})

            result = requests.Response()
            result.status_code = 200
            result._content = json.dumps(
                {"id_token": token, "access_token": "private-token"}
            ).encode()
            return result

        monkeypatch.setattr(requests, "post", exchange)
        monkeypatch.setattr(
            jwt.PyJWKClient,
            "fetch_data",
            lambda self: {
                "keys": [
                    dict(
                        jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key(), as_dict=True),
                        kid="test",
                        use="sig",
                        alg="RS256",
                    )
                ]
            },
        )
        return client.get(
            f"/api/auth/oauth/{provider_id}/callback",
            query_string={"state": params["state"], "code": "approved"},
        )

    return claims, authorize


def test_s003_s004_s007_s010_s012(client, provider) -> None:
    claims, authorize = provider
    assert authorize().location == "/"
    original = client.get("/api/auth/me").json
    assert original["display_name"] == "New User"
    client.post("/api/auth/logout")
    assert (
        client.post(
            "/api/auth/login", json={"email": claims["email"], "password": "random-password"}
        ).status_code
        == 401
    )
    claims["email"] = "changed@example.com"
    assert authorize().location == "/"
    assert client.get("/api/auth/me").json == original


@pytest.mark.parametrize("name", [None, "   ", "a" * 51])
def test_s006(client, provider, name) -> None:
    claims, authorize = provider
    claims["name"] = name
    authorize()
    assert client.get("/api/auth/me").json["display_name"] == "Theseus user"


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("email", None, "email"),
        ("nonce", "wrong", "invalid"),
        ("aud", "other", "invalid"),
        ("iss", "other", "invalid"),
        ("exp", 1, "invalid"),
    ],
)
def test_s013_s019_s028(client, provider, field, value, error) -> None:
    claims, authorize = provider
    claims[field] = value
    assert error in authorize().location
    assert client.get("/api/auth/me").status_code == 401


def test_s005_s011(client, provider) -> None:
    claims, authorize = provider
    account = client.post(
        "/api/auth/register",
        json={
            "display_name": "Original",
            "email": "Mixed.Case@example.com",
            "password": "safe-password",
        },
    ).json
    client.post("/api/auth/logout")
    claims["email"] = "mixed.case@example.com"
    assert "existing" in authorize().location
    assert client.get("/api/auth/me").status_code == 401
    claims["email"] = "other@example.com"
    authorize()
    linked = client.get("/api/auth/me").json
    assert linked["id"] != account["id"]
    client.post("/api/auth/logout")
    claims["email"] = "mixed.case@example.com"
    authorize()
    assert client.get("/api/auth/me").json == linked


def test_s016_timeout(client) -> None:
    from datetime import UTC, datetime, timedelta

    params = start(client)
    store = client.application.extensions["oauth_attempts"]
    with client.session_transaction() as session:
        store.items[session["oauth_attempt"]]["expires"] = datetime.now(UTC) - timedelta(seconds=1)
    result = client.get("/api/auth/oauth/google/callback", query_string={"state": params["state"]})
    assert "timeout" in result.location
    assert client.get("/api/auth/me").status_code == 401


def test_s018_suspended(client, provider) -> None:
    claims, authorize = provider
    authorize()
    repo = client.application.extensions["container"].identity.repository
    account = repo.find_identity("https://provider.example", claims["sub"])
    account.status = "suspended"
    client.post("/api/auth/logout")
    assert "unavailable" in authorize().location
    assert client.get("/api/auth/me").status_code == 401


@pytest.mark.parametrize("condition", ["bad_signature", "expired", "redeemed"])
def test_s019_invalid_exchange(client, provider, condition, caplog) -> None:
    _, authorize = provider
    options = (
        {"bad_signature": True} if condition == "bad_signature" else {"code_status": condition}
    )
    assert "invalid" in authorize(**options).location
    assert client.get("/api/auth/me").status_code == 401
    assert "Invalid credentials attempt" in caplog.text


def test_s019_missing_state(client) -> None:
    start(client)
    assert "invalid" in client.get("/api/auth/oauth/google/callback?code=unused").location


@pytest.mark.parametrize("success", [True, False])
def test_s027_s028_minimal_retention(client, provider, success, caplog) -> None:
    claims, authorize = provider
    claims["picture"] = "private-profile-marker"
    if not success:
        claims["nonce"] = "wrong"
    response = authorize()
    repo = client.application.extensions["container"].identity.repository
    with client.session_transaction() as session:
        retained = repr(dict(session))
    retained += repr([vars(u) for u in repo.db]) + repr(repo.identities)
    retained += repr(client.application.extensions["oauth_attempts"].items)
    retained += caplog.text + response.get_data(as_text=True)
    for marker in ("private-profile-marker", "private-token", "eyJ"):
        assert marker not in retained
    assert len(repo.db) == int(success)
    if success:
        assert repo.db[0].verified is False


def test_s023_audit_parity(client, provider, caplog) -> None:
    # Password login currently emits no application-level success audit event.
    body = {"email": "password@example.com", "display_name": "Reader", "password": "test-password"}
    client.post("/api/auth/register", json=body)
    client.post("/api/auth/logout")
    caplog.clear()
    assert client.post("/api/auth/login", json=body).status_code == 200
    expected = [(r.name, r.msg) for r in caplog.records]
    client.post("/api/auth/logout")
    caplog.clear()
    assert provider[1]().location == "/"
    assert [(r.name, r.msg) for r in caplog.records] == expected


def test_link_requires_initiating_session(client) -> None:
    body = {"email": "first@example.com", "display_name": "Reader", "password": "test-password"}
    client.post("/api/auth/register", json=body)
    assert client.post("/api/auth/oauth/google/link").status_code == 403
    csrf = client.get("/api/auth/oauth/providers").json["csrf"]
    result = client.post("/api/auth/oauth/google/link", headers={"X-CSRF-Token": csrf})
    state = parse_qs(urlsplit(result.json["location"]).query)["state"][0]
    client.post("/api/auth/logout")
    client.post("/api/auth/register", json=dict(body, email="second@example.com"))
    result = client.get(
        "/api/auth/oauth/google/callback", query_string={"code": "unused", "state": state}
    )
    assert "invalid" in result.location
    assert not client.application.extensions["container"].identity.repository.identities


def test_s024_linked_identity_stays_with_owner(client, provider) -> None:
    claims, authorize = provider
    authorize()
    original = client.get("/api/auth/me").json
    client.post("/api/auth/logout")
    other = client.post(
        "/api/auth/register",
        json={"email": "other@example.com", "display_name": "Other", "password": "test-password"},
    ).json
    assert "existing" in authorize(link=True).location
    assert client.get("/api/auth/me").json["id"] == other["id"]
    client.post("/api/auth/logout")
    authorize()
    assert client.get("/api/auth/me").json == original


def test_s012_unverified_email(client, provider) -> None:
    claims, authorize = provider
    assert claims["email_verified"] is False
    assert authorize().location == "/"
    assert client.get("/api/auth/me").json["email"] == claims["email"]


@pytest.mark.parametrize(
    ("offset", "lifetime", "accepted"), [(30, 120, True), (180, 300, False), (0, -1, False)]
)
def test_provider_clock_skew(client, provider, offset, lifetime, accepted) -> None:
    import time

    claims, authorize = provider
    now = int(time.time())
    claims.update(iat=now + offset, nbf=now + offset, exp=now + lifetime)
    result = authorize()
    assert (result.location == "/") is accepted
    assert client.get("/api/auth/me").status_code == (200 if accepted else 401)


def test_only_google_is_available_even_with_legacy_configuration(client) -> None:
    assert client.get("/api/auth/oauth/providers").json["providers"] == ["google"]
    assert client.get("/api/auth/oauth/microsoft/start").status_code == 404


def test_s032_google_connection_failure(client, monkeypatch) -> None:
    import requests

    def unreachable(*args: object, **kwargs: object) -> None:
        raise requests.ConnectionError()

    monkeypatch.setattr(requests, "post", unreachable)
    params = start(client)
    response = client.get(
        "/api/auth/oauth/google/callback", query_string={"state": params["state"], "code": "test"}
    )
    assert "auth_error=connection" in response.location
    assert client.get("/api/auth/me").status_code == 401


def test_s031_expired_attempt_after_store_cleanup(client) -> None:
    params = start(client)
    with client.session_transaction() as session:
        session["oauth_expires"] = 1
        client.application.extensions["oauth_attempts"].take(session["oauth_attempt"])
    response = client.get(
        "/api/auth/oauth/google/callback", query_string={"state": params["state"]}
    )
    assert "auth_error=timeout" in response.location
    assert client.get("/api/auth/me").status_code == 401


def test_s035_interactive_fallback_is_fresh_and_single_use(client, provider) -> None:
    claims, authorize = provider
    assert authorize().location == "/"
    client.post("/api/auth/logout")
    first = start(client)
    assert first["prompt"] == "none"
    assert first["login_hint"] == claims["sub"]
    route = "/api/auth/oauth/google/callback"
    result = client.get(route, query_string={"state": first["state"], "error": "consent_required"})
    second = parse_qs(urlsplit(result.location).query)
    assert "prompt" not in second
    assert second["login_hint"] == [claims["sub"]]
    for key in ("state", "nonce", "code_challenge"):
        assert second[key][0] != first[key]
    result = client.get(
        route, query_string={"state": second["state"][0], "error": "consent_required"}
    )
    assert result.location.startswith("/?auth_error=")
    assert client.get("/api/auth/me").status_code == 401


def test_s034_silent_sign_in_requires_the_same_verified_subject(client, provider) -> None:
    claims, authorize = provider
    assert authorize().location == "/"
    client.post("/api/auth/logout")
    claims["sub"] = "different-subject"
    assert "auth_error=invalid" in authorize().location
    assert client.get("/api/auth/me").status_code == 401


def test_s036_s037_remember_last_google_email(client, provider) -> None:
    claims, authorize = provider
    route = "/api/auth/oauth/providers"
    assert client.get(route).json.get("remembered_google_email") is None
    assert authorize().location == "/"
    client.post("/api/auth/logout")
    assert client.get(route).json.get("remembered_google_email") == claims["email"]
    assert start(client)["login_hint"] == claims["sub"]
