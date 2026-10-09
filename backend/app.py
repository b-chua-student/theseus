from pathlib import Path
from flask import Flask, jsonify, request, Response # noqa: F401
from test_database import client # noqa: F401

app = Flask(import_name=__name__)

REPO_DIR = Path(__file__).parent / "repository"

@app.get('/')
def get_all_documents() -> tuple[Response, int]:
    try:
        documents = [file.name for file in REPO_DIR.iterdir() if file.is_file()]
        return jsonify({
            "message": "Retrieved files successfully",
            "documents": documents,
        }), 200
    except Exception:
        return jsonify({"message": "Error: failed retrieving files"}), 500        

if __name__ == '__main__':
    app.run(port=5000, debug=True)
