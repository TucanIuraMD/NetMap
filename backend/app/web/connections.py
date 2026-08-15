from __future__ import annotations

from flask import Blueprint, render_template, request

from .api_client import ApiError, api_delete, api_get, api_post, api_put
from .helpers import device_display_name, index_by_id

connections_bp = Blueprint("connections", __name__, url_prefix="/connections")

CONNECTION_TYPES = ["network", "ethernet", "fiber", "wifi", "virtual", "other"]


def _connections_with_names() -> list[dict]:
    connections = api_get("/connections")
    devices_by_id = index_by_id(api_get("/devices"))
    ports_by_id = index_by_id(api_get("/ports"))

    for connection in connections:
        source = devices_by_id.get(connection["source_device_id"])
        target = devices_by_id.get(connection["target_device_id"])
        source_port = ports_by_id.get(connection.get("source_port_id"))
        target_port = ports_by_id.get(connection.get("target_port_id"))

        connection["source_name"] = (
            device_display_name(source) if source else "—"
        )
        connection["target_name"] = (
            device_display_name(target) if target else "—"
        )
        connection["source_port_label"] = (
            f"{source_port['port_number']}/{source_port['protocol']}"
            if source_port else "—"
        )
        connection["target_port_label"] = (
            f"{target_port['port_number']}/{target_port['protocol']}"
            if target_port else "—"
        )

    return connections


@connections_bp.get("")
def list_connections():
    return render_template(
        "connections/list.html",
        connections=_connections_with_names(),
        active_page="connections",
    )


@connections_bp.get("/new")
def new_connection_form():
    devices = api_get("/devices")
    return render_template(
        "connections/_form.html",
        connection=None,
        devices=devices,
        connection_types=CONNECTION_TYPES,
        source_ports=[],
        target_ports=[],
        error=None,
    )


@connections_bp.get("/<int:connection_id>/edit")
def edit_connection_form(connection_id: int):
    try:
        connection = api_get(f"/connections/{connection_id}")
    except ApiError as exc:
        return (
            f'<div class="modal-header"><h5 class="modal-title">Not found</h5>'
            f'<button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>'
            f'<div class="modal-body"><div class="alert alert-danger mb-0">'
            f"{exc.message}</div></div>",
            exc.status_code,
        )

    devices = api_get("/devices")
    all_ports = api_get("/ports")

    source_ports = [
        p for p in all_ports
        if p["device_id"] == connection["source_device_id"]
    ]
    target_ports = [
        p for p in all_ports
        if p["device_id"] == connection["target_device_id"]
    ]

    return render_template(
        "connections/_form.html",
        connection=connection,
        devices=devices,
        connection_types=CONNECTION_TYPES,
        source_ports=source_ports,
        target_ports=target_ports,
        error=None,
    )


@connections_bp.get("/port-options")
def port_options():
    """Cascading <select> partial: ports belonging to a device.

    Used by the create/edit connection form via hx-get (query param
    ``device_id``), triggered when the source/target device select
    changes.
    """
    device_id = request.args.get("device_id", type=int)

    ports = [
        p for p in api_get("/ports")
        if device_id is not None and p["device_id"] == device_id
    ]
    return render_template("connections/_port_options.html", ports=ports)


def _connection_form_payload() -> dict:
    def optional_int(field: str) -> int | None:
        value = request.form.get(field)
        return int(value) if value else None

    return {
        "source_device_id": request.form.get("source_device_id", type=int),
        "target_device_id": request.form.get("target_device_id", type=int),
        "source_port_id": optional_int("source_port_id"),
        "target_port_id": optional_int("target_port_id"),
        "connection_type": request.form.get("connection_type", "network"),
        "description": request.form.get("description", "").strip() or None,
        "is_active": request.form.get("is_active") == "on",
    }


@connections_bp.post("")
def create_connection():
    payload = _connection_form_payload()

    try:
        api_post("/connections", payload)
    except ApiError as exc:
        devices = api_get("/devices")
        return render_template(
            "connections/_form.html",
            connection=payload,
            devices=devices,
            connection_types=CONNECTION_TYPES,
            source_ports=[],
            target_ports=[],
            error=exc.message,
        ), exc.status_code

    response = render_template(
        "connections/_table.html", connections=_connections_with_names()
    )
    return response, 200, {"HX-Trigger": "connection-saved"}


@connections_bp.put("/<int:connection_id>")
def update_connection(connection_id: int):
    payload = _connection_form_payload()

    try:
        api_put(f"/connections/{connection_id}", payload)
    except ApiError as exc:
        devices = api_get("/devices")
        payload["id"] = connection_id
        return render_template(
            "connections/_form.html",
            connection=payload,
            devices=devices,
            connection_types=CONNECTION_TYPES,
            source_ports=[],
            target_ports=[],
            error=exc.message,
        ), exc.status_code

    response = render_template(
        "connections/_table.html", connections=_connections_with_names()
    )
    return response, 200, {"HX-Trigger": "connection-saved"}


@connections_bp.delete("/<int:connection_id>")
def delete_connection(connection_id: int):
    try:
        api_delete(f"/connections/{connection_id}")
    except ApiError as exc:
        return (
            f'<div class="alert alert-danger py-2 mb-2">{exc.message}</div>',
            exc.status_code,
        )

    return render_template(
        "connections/_table.html", connections=_connections_with_names()
    )
