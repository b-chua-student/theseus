import os

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request
from test_database import client  # noqa: F401

from manifold import Manifold

load_dotenv()

app = Flask(import_name=__name__)

@app.get("/api/documents")
def get_all_document_metadata() -> tuple[Response, int]:
    documents = Manifold.list_documents()
    return jsonify(documents), 200

@app.post("/api/save")
def save_document() -> tuple[Response, int]:
    raw_json: dict = request.get_json()
    document_id = raw_json.get("document_id")
    raw_html = raw_json.get("content")

    if not isinstance(document_id, str) or not isinstance(raw_html, str):
        return jsonify(message="Invalid payload."), 400

    manifold = Manifold(document_id)

    try:
        manifold.commit(document_id, raw_html, "sample user", "sampleuser@email.com", "first commit")
    except ValueError as e:
        print(e, flush=True)
        return jsonify(message="Save failed"), 400

    return jsonify(message=""), 200

@app.get("/api/documents/<id>")
def load_document(id: str) -> tuple[Response, int]:
    print(id, flush=True)
    manifold = Manifold(id)

    try:
        file_data = manifold.get_document()
    except KeyError as e:
        print(e, flush=True)
        return jsonify(content=""), 200

    file_content = file_data.get("file_content")

    return jsonify(content=file_content), 200

if __name__ == '__main__':
    app.run(
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "False").lower() == "true" # Return true if environment variable value is true, else false.
    )
