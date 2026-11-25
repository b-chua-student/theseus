"""Run Theseus over HTTPS alongside a loopback-only OIDC fixture for Playwright."""

import base64
import hashlib
import io
import logging
import os
import secrets
import sys
import time
from pathlib import Path
from threading import Thread
from urllib.parse import urlencode

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from flask import Flask, jsonify, redirect, render_template_string, request, send_from_directory
from werkzeug.serving import make_server

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from bootstrap.app import create_app

APP_PORT = int(os.environ.get("THESEUS_PREVIEW_PORT", "5173"))
APP = f"https://127.0.0.1:{APP_PORT}"
ISSUER = "http://127.0.0.1:5119"
provider = Flask("controlled_provider")
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
codes = {}
tokens = []
log = io.StringIO()
logging.getLogger().addHandler(logging.StreamHandler(log))
logging.getLogger().setLevel(logging.INFO)


@provider.route("/authorize", methods=["GET", "POST"])
def authorize():
    if request.method == "GET":
        return render_template_string("""
          <h1>Authorize Theseus</h1><form method="post">
          <label>Email<input name="email" required></label>
          <button>Continue</button></form>""")
    code = secrets.token_urlsafe()
    codes[code] = dict(email=request.form["email"], **request.args)
    return redirect(
        request.args["redirect_uri"]
        + "?"
        + urlencode({"code": code, "state": request.args["state"]})
    )


@provider.post("/token")
def token():
    auth = codes.pop(request.form["code"], None)
    if not auth:
        return jsonify(error="invalid_grant"), 400
    verifier = request.form["code_verifier"].encode()
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier).digest()).decode().rstrip("=")
    if challenge != auth["code_challenge"] or auth["redirect_uri"] != request.form["redirect_uri"]:
        return jsonify(error="invalid_grant"), 400
    now = int(time.time())
    signed = jwt.encode(
        dict(
            iss=ISSUER,
            sub=auth["email"],
            email=auth["email"],
            name="New User",
            aud="theseus",
            email_verified=False,
            iat=now,
            exp=now + 120,
            nonce=auth["nonce"],
        ),
        key,
        algorithm="RS256",
        headers={"kid": "fixture"},
    )
    access = secrets.token_urlsafe()
    tokens.extend([signed, access])
    return jsonify(id_token=signed, access_token=access)


@provider.get("/keys")
def keys():
    public = jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key(), as_dict=True)
    return jsonify(keys=[dict(public, kid="fixture", use="sig", alg="RS256")])


configs = {
    p: dict(
        issuer=ISSUER,
        authorization_endpoint=ISSUER + "/authorize",
        token_endpoint=ISSUER + "/token",
        jwks_uri=ISSUER + "/keys",
        client_id="theseus",
        client_secret="fixture",
        redirect_uri=f"{APP}/api/auth/oauth/{p}/callback",
    )
    for p in ("google", "microsoft")
}
app = create_app({"TESTING": True, "OAUTH_PROVIDERS": configs, "SESSION_COOKIE_SECURE": True})
dist = ROOT / "frontend" / "dist"
app.static_folder = str(dist / "assets")
app.view_functions["index"] = lambda: send_from_directory(dist, "index.html")
fallback = app.view_functions["frontend_fallback"]
app.view_functions["frontend_fallback"] = lambda path: (
    fallback(path)
    if path.startswith(("api/", "assets/"))
    else send_from_directory(dist, "index.html")
)


@provider.post("/check-exposure")
def check_exposure():
    evidence = request.get_data(as_text=True) + log.getvalue()
    return jsonify(issued=bool(tokens), exposed=any(t in evidence for t in tokens))


if __name__ == "__main__":
    server = make_server("127.0.0.1", 5119, provider, threaded=True)
    Thread(target=server.serve_forever, daemon=True).start()
    app.run(host="127.0.0.1", port=APP_PORT, ssl_context="adhoc", threaded=True)
