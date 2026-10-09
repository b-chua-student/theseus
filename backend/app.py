from flask import Flask, request
from test_database import client

app = Flask(import_name=__name__)

@app.get('/api/new_document')
def new_document() -> tuple[dict[str, str], int]:
    return {"message": "Created new document"}, 200 

if __name__ == '__main__':
    app.run(port=5000, debug=True)
