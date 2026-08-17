from flask import Flask, redirect, render_template, url_for

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
from .web import web_bp
from .web.api_client import ApiError
from .scheduler import init_scheduler, should_start_scheduler


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    if should_start_scheduler(app):
        init_scheduler(app)

    app.register_blueprint(api_v1, url_prefix="/api/v1")
    app.register_blueprint(web_bp)

    @app.get("/")
    def index():
        # Previously returned a static placeholder ("Foundation
        # v0.1.0"). Now that a real Dashboard exists (UI Iteration
        # 1), the root path takes the user straight to it.
        return redirect(url_for("web.dashboard.dashboard"))

    @app.get("/api/v1/health")
    def health():
        return {
            "status": "ok",
            "project": "NetMap",
            "version": "0.1.0",
        }

    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        # Safety net: the UI layer calls the REST API internally
        # (see app/web/api_client.py). Routes that render into a
        # modal or a small HTMX target catch ApiError themselves
        # (see app/web/devices.py, networks.py, connections.py) so
        # they degrade into a small inline alert rather than a full
        # page. This handler only catches anything left unhandled.
        return (
            render_template("errors/404.html", message=error.message),
            error.status_code,
        )

    return app