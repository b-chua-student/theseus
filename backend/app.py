from flask import Flask, request
from test_database import client
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(import_name=__name__)

if __name__ == '__main__':
    app.run(
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "False").lower() == "true" # Return true if environment variable value is true, else false.
    )
