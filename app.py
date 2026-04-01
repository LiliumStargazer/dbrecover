# ./app.py
from flask import Flask
from dotenv import load_dotenv
from services.dbrecover.routes import bp

load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(bp)
    return app


if __name__ == "__main__":
    app = create_app()
    # Note: in production, we run this app with Gunicorn, so this block is not executed.
    app.run(host="0.0.0.0", port=5050)


import os

print(f"[app-start] pid={os.getpid()}")
