import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "netmap-dev")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///netmap.db",
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False