from flask import Flask

from config import Config
from .extensions import db, migrate
from .models.site import Site
from .models.network import Network
from .models.device import Device
from .models.ip_address import IPAddress

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    @app.get("/")
    def index():
        return "<h1>NetMap</h1><p>Foundation v0.1.0</p>"

    @app.get("/api/v1/health")
    def health():
        return {
            "status": "ok",
            "project": "NetMap",
            "version": "0.1.0",
        }

    return app
