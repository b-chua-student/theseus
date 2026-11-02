from bootstrap.app import create_app

from dotenv import load_dotenv
import os

load_dotenv()

app = create_app(config={"SECRET_KEY": os.getenv("SECRET_KEY")})

if __name__ == "__main__":
    app.run(debug=True)
