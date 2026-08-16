"""Internal REST API client used by the Web UI layer.

The Web UI must never query SQLAlchemy models directly (see
docs/03_API.md, section 30: "The Web UI is only a client of the
REST API"). Since the UI and the API live in the same Flask process,
we avoid a real network round-trip and instead call the existing
``/api/v1`` blueprint through Flask's built-in test client. This
keeps the API as the single source of truth without introducing a
new dependency (e.g. `requests`) or a second HTTP server hop.
"""

from __future__ import annotations

from typing import Any

from flask import current_app


class ApiError(Exception):
    """Raised when the internal API call returns an error response."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"{status_code}: {message}")


def _client():
    return current_app.test_client()


def _handle_response(response) -> Any:
    payload = response.get_json(silent=True)

    if response.status_code >= 400:
        message = "Unknown error"

        if isinstance(payload, dict):
            message = payload.get("error", message)

        raise ApiError(response.status_code, message)

    return payload


def api_get(path: str, params: dict | None = None) -> Any:
    response = _client().get(f"/api/v1{path}", query_string=params)
    return _handle_response(response)


def api_post(path: str, data: dict) -> Any:
    response = _client().post(f"/api/v1{path}", json=data)
    return _handle_response(response)


def api_put(path: str, data: dict) -> Any:
    response = _client().put(f"/api/v1{path}", json=data)
    return _handle_response(response)


def api_delete(path: str) -> None:
    response = _client().delete(f"/api/v1{path}")
    _handle_response(response)
