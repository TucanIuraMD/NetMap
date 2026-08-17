import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "netmap-dev")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///netmap.db",
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MONITORING_ENABLED = os.getenv(
        "MONITORING_ENABLED",
        "true",
    ).lower() in {"1", "true", "yes", "on"}

    MONITORING_INTERVAL_MINUTES = int(
        os.getenv("MONITORING_INTERVAL_MINUTES", "5")
    )