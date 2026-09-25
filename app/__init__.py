import os
from flask import Flask


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

    from app.routes.main_routes import main
    app.register_blueprint(main)

    return app