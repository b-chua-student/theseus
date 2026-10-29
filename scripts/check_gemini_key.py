# ../scripts/check_gemini_key.py
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

ENV_PATH = Path(__file__).resolve().parent.parent / "backend" / ".env"
print("loading:", ENV_PATH, "exists:", ENV_PATH.exists())

load_dotenv(ENV_PATH, override=True)

key = os.environ.get("GEMINI_API_KEY", "")
print(f"key loaded: {bool(key)}, length: {len(key)}, prefix: {key[:4]!r}")

if not key or key == "CHANGE_ME":
    raise SystemExit("No real key found in .env")

client = genai.Client(
    api_key=key,
    http_options=types.HttpOptions(timeout=30_000),  # milliseconds
)

try:
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents="Reply with the single word: ok",
    )
except Exception as exc:
    raise SystemExit(f"FAILED: {exc}")

print("OK:", response.text)
