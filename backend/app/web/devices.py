from __future__ import annotations

from flask import Blueprint, render_template, request

from .api_client import ApiError, api_delete, api_get, api_post, api_put
from .helpers import (
    device_connections,
    device_display_name,
    device_interfaces,
    device_ip_addresses,
    device_ports,
    device_type_options,
    filter_devices,
    index_by_id,
    paginate,
    sort_devices,
)

devices_bp = Blueprint("devices", __name__, url_prefix="/devices")

DEVICE_TYPES = [
    "router",
    "switch",
    "server",
    "nas",
    "camera",
    "printer",
    "ap",
    "esp32",
    "pc",
    "laptop",
    "phone",
    "unknown",
    "other",
]


def _primary_ip_by_device(
    devices: list[dict],
    interfaces: list[dict],
    ip_addresses: list[dict],
) -> dict[int, str]:
    interfaces_by_device: dict[int, list[int]] = {}

    for interface in interfaces:
        interfaces_by_device.setdefault(interface["device_id"], []).append(
            interface["id"]
        )

    primary_by_interface: dict[int, str] = {}

    for ip in ip_addresses:
        if ip.get("is_primary"):
            primary_by_interface[ip["interface_id"]] = ip["address"]

    result: dict[int, str] = {}

    for device in devices:
        for interface_id in interfaces_by_device.get(device["id"], []):
            if interface_id in primary_by_interface:
                result[device["id"]] = primary_by_interface[interface_id]
                break

    return result


def _filtered_devices() -> tuple[list[dict], dict]:
    devices = api_get("/devices")
    networks = api_get("/networks")
    networks_by_id = index_by_id(networks)
    ports = api_get("/ports")
    interfaces = api_get("/interfaces")
    ip_addresses = api_get("/ip-addresses")

    ports_count_by_device: dict[int, int] = {}
    for port in ports:
        ports_count_by_device[port["device_id"]] = (
            ports_count_by_device.get(port["device_id"], 0) + 1
        )

    primary_ip = _primary_ip_by_device(devices, interfaces, ip_addresses)

    filters = {
        "search": request.args.get("search", ""),
        "network_id": request.args.get("network_id", ""),
        "device_type": request.args.get("device_type", ""),
        "status": request.args.get("status", ""),
    }
    sort = request.args.get("sort", "")

    result = filter_devices(devices, **filters)
    result = sort_devices(result, sort)

    for device in result:
        network = networks_by_id.get(device.get("network_id"))
        device["network_name"] = network["name"] if network else "—"
        device["display"] = device_display_name(device)
        device["ports_count"] = ports_count_by_device.get(device["id"], 0)
        device["primary_ip"] = primary_ip.get(device["id"])

    page = paginate(
        result,
        page=request.args.get("page", 1, type=int),
        page_size=request.args.get("page_size", 50, type=int),
    )

    context = {
        "filters": filters,
        "sort": sort,
        "networks": networks,
        "device_types": device_type_options(devices),
        "pagination": page,
    }

    return page["items"], context


@devices_bp.get("")
def list_devices():
    devices, context = _filtered_devices()
    return render_template(
        "devices/list.html", devices=devices, active_page="devices", **context
    )


@devices_bp.get("/table")
def devices_table():
    devices, context = _filtered_devices()
    return render_template(
        "devices/_table.html", devices=devices, **context
    )


@devices_bp.get("/new")
def new_device_form():
    networks = api_get("/networks")
    return render_template(
        "devices/_form.html",
        device=None,
        networks=networks,
        device_types=DEVICE_TYPES,
        error=None,
    )


@devices_bp.get("/<int:device_id>/edit")
def edit_device_form(device_id: int):
    try:
        device = api_get(f"/devices/{device_id}")
    except ApiError as exc:
        return (
            f'<div class="modal-header"><h5 class="modal-title">Not found</h5>'
            f'<button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>'
            f'<div class="modal-body"><div class="alert alert-danger mb-0">'
            f"{exc.message}</div></div>",
            exc.status_code,
        )

    networks = api_get("/networks")
    return render_template(
        "devices/_form.html",
        device=device,
        networks=networks,
        device_types=DEVICE_TYPES,
        error=None,
    )


def _device_form_payload() -> dict:
    is_active = request.form.get("is_active") == "on"

    return {
        "name": request.form.get("name", "").strip(),
        "display_name": request.form.get("display_name", "").strip() or None,
        "hostname": request.form.get("hostname", "").strip() or None,
        "network_id": request.form.get("network_id", type=int),
        "device_type": request.form.get("device_type") or None,
        "description": request.form.get("description", "").strip() or None,
        "is_active": is_active,
    }


@devices_bp.post("")
def create_device():
    payload = _device_form_payload()

    try:
        api_post("/devices", payload)
    except ApiError as exc:
        networks = api_get("/networks")
        return render_template(
            "devices/_form.html",
            device=payload,
            networks=networks,
            device_types=DEVICE_TYPES,
            error=exc.message,
        ), exc.status_code

    devices, context = _filtered_devices()
    response = render_template(
        "devices/_table.html", devices=devices, **context
    )
    headers = {"HX-Trigger": "device-saved"}
    return response, 200, headers


@devices_bp.put("/<int:device_id>")
def update_device(device_id: int):
    payload = _device_form_payload()

    try:
        api_put(f"/devices/{device_id}", payload)
    except ApiError as exc:
        networks = api_get("/networks")
        payload["id"] = device_id
        return render_template(
            "devices/_form.html",
            device=payload,
            networks=networks,
            device_types=DEVICE_TYPES,
            error=exc.message,
        ), exc.status_code

    # Bugfix: the edit form now targets #nm-modal-content (see
    # devices/_form.html), which exists on every page. To keep the
    # Devices List table live-updating like before, the refreshed
    # table is returned as an out-of-band swap targeting
    # #devices-table-wrapper — it updates the table when that element
    # is present (List page) and is silently skipped when it is not
    # (Device Details page). HX-Trigger still closes the modal either way.
    devices, context = _filtered_devices()
    table_html = render_template(
        "devices/_table.html", devices=devices, **context
    )
    response = (
        f'<div id="devices-table-wrapper" hx-swap-oob="true">'
        f"{table_html}</div>"
    )
    headers = {"HX-Trigger": "device-saved"}
    return response, 200, headers


@devices_bp.delete("/<int:device_id>")
def delete_device(device_id: int):
    try:
        api_delete(f"/devices/{device_id}")
    except ApiError as exc:
        return (
            f'<div class="alert alert-danger py-2 mb-2">'
            f"{exc.message}</div>",
            exc.status_code,
        )

    devices, context = _filtered_devices()
    return render_template("devices/_table.html", devices=devices, **context)


@devices_bp.get("/<int:device_id>")
def device_details(device_id: int):
    try:
        device = api_get(f"/devices/{device_id}")
    except ApiError as exc:
        return render_template("errors/404.html", message=exc.message), exc.status_code

    networks = api_get("/networks")
    all_ports = api_get("/ports")
    all_interfaces = api_get("/interfaces")
    all_ip_addresses = api_get("/ip-addresses")
    all_connections = api_get("/connections")
    all_devices = api_get("/devices")

    network = index_by_id(networks).get(device.get("network_id"))
    interfaces = device_interfaces(all_interfaces, device_id)
    ip_addresses = device_ip_addresses(all_ip_addresses, interfaces)
    ports = device_ports(all_ports, device_id)
    connections = device_connections(all_connections, device_id)
    devices_by_id = index_by_id(all_devices)

    for connection in connections:
        source = devices_by_id.get(connection["source_device_id"])
        target = devices_by_id.get(connection["target_device_id"])
        connection["source_name"] = (
            device_display_name(source) if source else "—"
        )
        connection["target_name"] = (
            device_display_name(target) if target else "—"
        )

    return render_template(
        "devices/details.html",
        device=device,
        display=device_display_name(device),
        network=network,
        interfaces=interfaces,
        ip_addresses=ip_addresses,
        ports=ports,
        connections=connections,
        active_page="devices",
    )
