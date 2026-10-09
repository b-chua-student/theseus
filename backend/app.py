from flask import Flask, jsonify, Response
from test_database import client

app = Flask(import_name=__name__)

@app.get('/')
def get_all_documents() -> tuple[Response, int]:
    try:
        documents = client.get_all_documents()
        return jsonify({
            "message": "Retrieved files successfully",
            "documents": documents,
        }), 200
    except Exception:
        return jsonify({"message": "Error: failed retrieving files"}), 500        

if __name__ == '__main__':
    app.run(port=5000, debug=True)
