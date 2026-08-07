from flask import Flask


def create_app() -> Flask:
    """Application Factory."""

    app = Flask(__name__)

    @app.get("/")
    def index():
        return "<h1>NetMap</h1><p>Foundation v0.1.0</p>"

    @app.get("/api/v1/health")
    def health():
        return {
            "status": "ok",
            "project": "NetMap",
            "version": "0.1.0"
        }

    return app