import os

from dotenv import load_dotenv
from flask import Flask, request  # noqa: F401

from test_database import client  # noqa: F401

load_dotenv()

app = Flask(import_name=__name__)

if __name__ == '__main__':
    app.run(
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "False").lower() == "true" # Return true if environment variable value is true, else false.
    )
