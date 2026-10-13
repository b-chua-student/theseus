import os

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request
from google import genai

from manifold import Manifold
from test_database import client  # noqa: F401

load_dotenv()

app = Flask(import_name=__name__)


@app.get("/api/documents")
def get_all_document_metadata() -> tuple[Response, int]:
    """Return metadata for all stored documents.

    Returns:
        A JSON list of document metadata and HTTP status 200.
    """
    documents = Manifold.list_documents()
    return jsonify(documents), 200


@app.post("/api/save")
def save_document() -> tuple[Response, int]:
    """Save a document by committing its HTML content.

    Expects a JSON payload with string fields ``document_id`` and ``content``.

    Returns:
        A JSON message and HTTP status 200 on success, or 400 if the payload
        is invalid or the commit fails.
    """
    raw_json = request.get_json()
    document_id = raw_json.get("document_id")
    raw_html = raw_json.get("content")

    if not isinstance(document_id, str) or not isinstance(raw_html, str):
        return jsonify(message="Invalid payload."), 400

    manifold = Manifold(document_id)

    try:
        manifold.commit(
            document_id, raw_html, "sample user", "sampleuser@email.com", "first commit"
        )
    except ValueError:
        return jsonify(message="Save failed"), 400

    return jsonify(message=""), 200


@app.get("/api/documents/<document_id>")
def load_document(document_id: str) -> tuple[Response, int]:
    """Load the content of a single document.

    Args:
        document_id: The unique identifier of the document.

    Returns:
        A JSON object with the document's ``content`` and HTTP status 200.
        Content is an empty string if the document does not exist.
    """
    manifold = Manifold(document_id)

    try:
        file_data = manifold.get_document()
    except KeyError:
        return jsonify(content=""), 200

    file_content = file_data.get("file_content")

    return jsonify(content=file_content), 200


@app.post("/api/chat")
def test_ai_call() -> tuple[str, int]:
    """Send a user message to Gemini and return its reply.

    Expects a JSON body with a "message" string.

    Returns:
        A tuple of a JSON response {"reply": str} and the HTTP status code.
    """
    raw_json = request.get_json()
    message = raw_json.get("message")

    ai = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    interaction = ai.interactions.create(model="gemini-3.8-flash", input=message)

    return jsonify(reply=interaction.output_text), 200


if __name__ == "__main__":
    app.run(
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "False").lower()
        == "true",  # Return true if environment variable value is true, else false.
    )
