from flask import Flask, request
from test_database import client

app = Flask(import_name=__name__)

@app.get('/api/get_all_documents')
def get_all_documents() -> tuple[dict[str, str], int]:
    try:
        return {"message": "Retrieved files successfully"}, 200
    except Exception:
        return {"message": "Error: failed retrieving files"}, 500        

if __name__ == '__main__':
    app.run(port=5000, debug=True)
