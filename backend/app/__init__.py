from flask import Flask

from config import Config
from .extensions import db, migrate

from .models.site import Site
from .models.network import Network
from .models.device import Device
from .models.interface import Interface
from .models.ip_address import IPAddress
from .models.port import Port
from .models.service import Service
from .models.connection import Connection

from .api.v1 import api_v1


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(api_v1, url_prefix="/api/v1")

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