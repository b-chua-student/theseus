from flask import Flask, request
from test_database import client

app = Flask(import_name=__name__)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
