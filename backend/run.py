import os

from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

from bootstrap.app import create_app

load_dotenv()

secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    # Without a secret key Flask cannot sign the session cookie, so every login
    # would fail later with an obscure error. Fail at startup with a clear one.
    raise RuntimeError("SECRET_KEY is not set. Set it in the environment or backend/.env.")

app = create_app(
    config={
        "SECRET_KEY": secret_key,
        # In production the site is served over HTTPS, so the cookie must be Secure.
        "SESSION_COOKIE_SECURE": os.getenv("SESSION_COOKIE_SECURE") == "1",
        "SESSION_COOKIE_SAMESITE": "Lax",
    }
)

# Behind a reverse proxy (Render) every request arrives from the proxy's IP, so
# without this the rate limiter would count *all* users as one client. Set
# TRUST_PROXY_HOPS to the number of proxies in front of the app (1 on Render); leave
# it unset locally, where trusting X-Forwarded-For would let clients spoof their IP.
if hops := int(os.getenv("TRUST_PROXY_HOPS", "0")):
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=hops, x_proto=hops, x_host=hops)  # type: ignore[method-assign]

if __name__ == "__main__":
    app.run(debug=True)
