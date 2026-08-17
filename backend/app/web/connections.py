from __future__ import annotations

from flask import Blueprint, render_template, request

from .api_client import ApiError, api_delete, api_get, api_post, api_put
from .helpers import (
    device_display_name,
    index_by_id,
    interface_display_label,
)
from app.api.v1.validation import CONNECTION_TYPES

connections_bp = Blueprint("connections", __name__, url_prefix="/connections")


def _connections_with_names(
    device_id: int | None = None,
) -> list[dict]:
    params = {"device_id": device_id} if device_id else None
    connections = api_get("/connections", params=params)

    # With query parameters the API returns a paginated envelope
    # ({items, ...}); without any it returns a bare array.
    if isinstance(connections, dict):
        connections = connections["items"]

    devices_by_id = index_by_id(api_get("/devices"))
    ports_by_id = index_by_id(api_get("/ports"))
    interfaces_by_id = index_by_id(api_get("/interfaces"))
    ip_addresses = api_get("/ip-addresses")

    primary_ip_by_interface: dict[int, str] = {}
    for ip in ip_addresses:
        if ip.get("is_primary"):
            primary_ip_by_interface[ip["interface_id"]] = ip["address"]

    def port_label(port: dict | None) -> str | None:
        if port is None:
            return None
        label = f"{port['port_number']}/{port['protocol']}"
        if port.get("display_name"):
            label += f" ({port['display_name']})"
        return label

    def interface_label(interface: dict | None) -> str | None:
        if interface is None:
            return None
        return interface_display_label(
            interface,
            primary_ip_by_interface.get(interface["id"]),
        )

    for connection in connections:
        source = devices_by_id.get(connection["source_device_id"])
        target = devices_by_id.get(connection["target_device_id"])
        source_port = ports_by_id.get(connection.get("source_port_id"))
        target_port = ports_by_id.get(connection.get("target_port_id"))
        source_interface = interfaces_by_id.get(
            connection.get("source_interface_id")
        )
        target_interface = interfaces_by_id.get(
            connection.get("target_interface_id")
        )

        connection["source_name"] = (
            device_display_name(source) if source else "—"
        )
        connection["target_name"] = (
            device_display_name(target) if target else "—"
        )
        connection["source_port_label"] = port_label(source_port)
        connection["target_port_label"] = port_label(target_port)
        connection["source_interface_label"] = interface_label(source_interface)
        connection["target_interface_label"] = interface_label(target_interface)
        connection["source_ip"] = (
            primary_ip_by_interface.get(
                connection["source_interface_id"]
            )
            if connection.get("source_interface_id") else None
        )
        connection["target_ip"] = (
            primary_ip_by_interface.get(
                connection["target_interface_id"]
            )
            if connection.get("target_interface_id") else None
        )

    return connections


@connections_bp.get("")
def list_connections():
    device_id = request.args.get("device_id", type=int)
    devices = api_get("/devices")
    return render_template(
        "connections/list.html",
        connections=_connections_with_names(device_id),
        devices=devices,
        selected_device_id=device_id,
        active_page="connections",
    )


@connections_bp.get("/table")
def connections_table():
    """Partial table used by the device filter via hx-get."""
    device_id = request.args.get("device_id", type=int)
    return render_template(
        "connections/_table.html",
        connections=_connections_with_names(device_id),
    )


@connections_bp.get("/new")
def new_connection_form():
    devices = api_get("/devices")
    return render_template(
        "connections/_form.html",
        connection=None,
        devices=devices,
        connection_types=CONNECTION_TYPES,
        source_interfaces=[],
        target_interfaces=[],
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
    all_interfaces = api_get("/interfaces")

    source_interfaces = [
        i for i in all_interfaces
        if i["device_id"] == connection["source_device_id"]
    ]
    target_interfaces = [
        i for i in all_interfaces
        if i["device_id"] == connection["target_device_id"]
    ]
    for iface in source_interfaces + target_interfaces:
        iface["label"] = interface_display_label(iface)
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
        source_interfaces=source_interfaces,
        target_interfaces=target_interfaces,
        source_ports=source_ports,
        target_ports=target_ports,
        error=None,
    )


@connections_bp.get("/interface-options")
def interface_options():
    """Cascading <select> partial: interfaces belonging to a device.

    Used by the create/edit connection form via hx-get (query param
    ``device_id``), triggered when the source/target device select
    changes.
    """
    device_id = request.args.get("device_id", type=int)

    interfaces = [
        i for i in api_get("/interfaces")
        if device_id is not None and i["device_id"] == device_id
    ]
    for iface in interfaces:
        iface["label"] = interface_display_label(iface)
    return render_template(
        "connections/_interface_options.html", interfaces=interfaces
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
        "source_interface_id": optional_int("source_interface_id"),
        "target_interface_id": optional_int("target_interface_id"),
        "source_port_id": optional_int("source_port_id"),
        "target_port_id": optional_int("target_port_id"),
        "connection_type": request.form.get("connection_type", "network"),
        "description": request.form.get("description", "").strip() or None,
        "is_active": request.form.get("is_active") == "on",
    }


def _current_device_filter() -> int | None:
    """Keep the active device filter across table refreshes."""
    return request.args.get("device_id", type=int)


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
            source_interfaces=[],
            target_interfaces=[],
            source_ports=[],
            target_ports=[],
            error=exc.message,
        ), exc.status_code

    response = render_template(
        "connections/_table.html", connections=_connections_with_names(_current_device_filter())
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
            source_interfaces=[],
            target_interfaces=[],
            source_ports=[],
            target_ports=[],
            error=exc.message,
        ), exc.status_code

    response = render_template(
        "connections/_table.html", connections=_connections_with_names(_current_device_filter())
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
        "connections/_table.html", connections=_connections_with_names(_current_device_filter())
    )
