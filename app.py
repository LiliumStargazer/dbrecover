# dbrecover/app.py  (SOLUZIONE A: Blueprint)
from flask import Flask
from dotenv import load_dotenv
from routes import bp

load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(bp)
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5050)
