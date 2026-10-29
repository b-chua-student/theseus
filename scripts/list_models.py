# ../scripts/list_models.py
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(Path(__file__).resolve().parent.parent / "backend" / ".env", override=True)

client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"],
    http_options=types.HttpOptions(timeout=30_000),  # milliseconds
)

for model in client.models.list():
    print(model.name, model.supported_actions)
