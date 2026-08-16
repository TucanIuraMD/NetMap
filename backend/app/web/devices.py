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
    index_by_id,
    interface_display_label,
    port_service_name,
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

INTERFACE_TYPES = [
    "ethernet",
    "wireless",
    "virtual",
    "bridge",
    "vlan",
    "bond",
    "tunnel",
    "other",
]

PORT_STATUSES = ["open", "closed", "filtered", "unknown"]
WEB_SCHEMES = ["http", "https"]


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
    networks = api_get("/networks")
    networks_by_id = index_by_id(networks)
    ports = api_get("/ports")
    interfaces = api_get("/interfaces")
    ip_addresses = api_get("/ip-addresses")
    connections = api_get("/connections")

    ports_count_by_device: dict[int, int] = {}
    ports_by_device: dict[int, list[dict]] = {}
    for port in ports:
        ports_count_by_device[port["device_id"]] = (
            ports_count_by_device.get(port["device_id"], 0) + 1
        )
        ports_by_device.setdefault(port["device_id"], []).append(port)

    interfaces_by_device: dict[int, list[dict]] = {}
    for interface in interfaces:
        interfaces_by_device.setdefault(interface["device_id"], []).append(
            interface
        )

    ip_count_by_interface: dict[int, int] = {}
    primary_by_interface: dict[int, str] = {}
    for ip in ip_addresses:
        ip_count_by_interface[ip["interface_id"]] = (
            ip_count_by_interface.get(ip["interface_id"], 0) + 1
        )
        if ip.get("is_primary"):
            primary_by_interface[ip["interface_id"]] = ip["address"]

    # Used by the per-card Links counter below.
    connections_count_by_device: dict[int, int] = {}
    for connection in connections:
        connections_count_by_device[connection["source_device_id"]] = (
            connections_count_by_device.get(
                connection["source_device_id"], 0
            ) + 1
        )
        connections_count_by_device[connection["target_device_id"]] = (
            connections_count_by_device.get(
                connection["target_device_id"], 0
            ) + 1
        )

    filters = {
        "search": request.args.get("search", ""),
        "network_id": request.args.get("network_id", ""),
        "device_type": request.args.get("device_type", ""),
        "status": request.args.get("status", ""),
        "links": request.args.get("links", ""),
    }
    sort = request.args.get("sort", "")

    # Filtering, sorting and pagination happen server-side in the API
    # (GET /api/v1/devices). The UI only enriches the returned page.
    params: dict = {k: v for k, v in filters.items() if v}
    if sort:
        params["sort"] = sort
    params["page"] = request.args.get("page", 1, type=int)
    params["per_page"] = request.args.get("page_size", 50, type=int)

    payload = api_get("/devices", params=params)
    result = payload["items"]

    primary_ip = _primary_ip_by_device(result, interfaces, ip_addresses)

    for device in result:
        device_id = device["id"]
        network = networks_by_id.get(device.get("network_id"))
        device["network_name"] = network["name"] if network else "—"
        device["display"] = device_display_name(device)
        device["ports_count"] = ports_count_by_device.get(device_id, 0)

        device["ports_preview"] = [
            {
                "port_number": port["port_number"],
                "protocol": port.get("protocol"),
                "display_name": port.get("display_name"),
                "service_name": port_service_name(port),
                "web_url": port.get("web_url"),
            }
            for port in sorted(
                ports_by_device.get(device_id, []),
                key=lambda p: (p.get("port_number") or 0),
            )
        ]

        device_ifaces = interfaces_by_device.get(device_id, [])
        device["interfaces_count"] = len(device_ifaces)
        device["ip_count"] = sum(
            ip_count_by_interface.get(interface["id"], 0)
            for interface in device_ifaces
        )
        device["connections_count"] = connections_count_by_device.get(
            device_id, 0
        )
        device["interfaces_preview"] = [
            {
                "name": interface["name"],
                "interface_type": interface.get("interface_type"),
                "primary_ip": primary_by_interface.get(interface["id"]),
            }
            for interface in sorted(
                device_ifaces,
                key=lambda i: (i.get("name") or "").lower(),
            )[:3]
        ]
        device["primary_ip"] = primary_ip.get(device_id)

    # The API returns pagination metadata; keep the shape the templates
    # expect (page / page_size / total / total_pages).
    pagination = {
        "page": payload["page"],
        "page_size": payload["per_page"],
        "total": payload["total"],
        "total_pages": payload["total_pages"],
    }

    # The type filter dropdown lists every distinct type across all
    # devices, regardless of the current filter/pagination window.
    all_devices = api_get("/devices")

    context = {
        "filters": filters,
        "sort": sort,
        "networks": networks,
        "device_types": device_type_options(all_devices),
        "pagination": pagination,
    }

    return result, context


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


def _device_details_context(device_id: int) -> dict:
    device = api_get(f"/devices/{device_id}")

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
    ports_by_id = index_by_id(all_ports)
    interfaces_by_id = index_by_id(all_interfaces)

    primary_ip_by_interface: dict[int, str] = {}
    for ip in all_ip_addresses:
        if ip.get("is_primary"):
            primary_ip_by_interface[ip["interface_id"]] = ip["address"]

    # Group IP addresses under their interface (each interface carries
    # its own list of IPs, so the Interfaces tab can render them inline).
    ip_addresses_by_interface: dict[int, list[dict]] = {}
    for ip in ip_addresses:
        ip_addresses_by_interface.setdefault(ip["interface_id"], []).append(
            ip
        )

    for interface in interfaces:
        interface["ip_addresses"] = sorted(
            ip_addresses_by_interface.get(interface["id"], []),
            key=lambda a: (a.get("is_primary") is not True, a.get("address") or ""),
        )
        primary = next(
            (
                ip["address"]
                for ip in interface["ip_addresses"]
                if ip.get("is_primary")
            ),
            None,
        )
        interface["primary_ip"] = primary

    # There is no Port -> IPAddress/Interface foreign key. A service port
    # binds to the device's primary IP, so the interface carrying it is the
    # port's host interface (the same rule the API uses for ``web_url``).
    # Attribute the device's ports to that interface so the Interfaces tab
    # can render them inline.
    primary_interface_id = next(
        (
            interface["id"]
            for interface in interfaces
            if interface.get("primary_ip")
        ),
        None,
    )

    for interface in interfaces:
        interface["service_ports"] = (
            ports if interface["id"] == primary_interface_id else []
        )

    for ip in ip_addresses:
        interface = interfaces_by_id.get(ip.get("interface_id"))
        ip["interface_name"] = interface["name"] if interface else None

    def _port_label(port: dict | None) -> str | None:
        if port is None:
            return None
        label = f"{port['port_number']}/{port['protocol']}"
        if port.get("display_name"):
            label += f" ({port['display_name']})"
        return label

    for connection in connections:
        source = devices_by_id.get(connection["source_device_id"])
        target = devices_by_id.get(connection["target_device_id"])
        connection["source_name"] = (
            device_display_name(source) if source else "—"
        )
        connection["target_name"] = (
            device_display_name(target) if target else "—"
        )
        source_interface = interfaces_by_id.get(
            connection.get("source_interface_id")
        )
        target_interface = interfaces_by_id.get(
            connection.get("target_interface_id")
        )
        connection["source_interface_name"] = (
            interface_display_label(
                source_interface,
                primary_ip_by_interface.get(source_interface["id"]),
            )
            if source_interface
            else None
        )
        connection["target_interface_name"] = (
            interface_display_label(
                target_interface,
                primary_ip_by_interface.get(target_interface["id"]),
            )
            if target_interface
            else None
        )
        connection["source_port_label"] = _port_label(
            ports_by_id.get(connection.get("source_port_id"))
        )
        connection["target_port_label"] = _port_label(
            ports_by_id.get(connection.get("target_port_id"))
        )

    return {
        "device": device,
        "display": device_display_name(device),
        "network": network,
        "interfaces": interfaces,
        "ip_addresses": ip_addresses,
        "ports": ports,
        "connections": connections,
        "active_page": "devices",
    }


@devices_bp.get("/<int:device_id>")
def device_details(device_id: int):
    try:
        context = _device_details_context(device_id)
    except ApiError as exc:
        return render_template("errors/404.html", message=exc.message), exc.status_code

    return render_template("devices/details.html", **context)


# --- Interfaces CRUD (device-scoped) ---


def _interfaces_section(device_id: int) -> str:
    context = _device_details_context(device_id)
    return render_template(
        "devices/_interfaces_section.html",
        device=context["device"],
        interfaces=context["interfaces"],
    )


@devices_bp.get("/<int:device_id>/interfaces/new")
def new_interface_form(device_id: int):
    device = api_get(f"/devices/{device_id}")
    return render_template(
        "devices/_interface_form.html",
        device=device,
        interface=None,
        interface_types=INTERFACE_TYPES,
        error=None,
    )


@devices_bp.post("/<int:device_id>/interfaces")
def create_interface(device_id: int):
    payload = {
        "device_id": device_id,
        "name": request.form.get("name", "").strip(),
        "interface_type": request.form.get("interface_type") or None,
        "mac_address": request.form.get("mac_address", "").strip() or None,
        "speed": request.form.get("speed", type=int),
        "mtu": request.form.get("mtu", type=int),
        "description": request.form.get("description", "").strip() or None,
        "is_active": request.form.get("is_active") == "on",
    }

    try:
        api_post("/interfaces", payload)
    except ApiError as exc:
        device = api_get(f"/devices/{device_id}")
        return render_template(
            "devices/_interface_form.html",
            device=device,
            interface=payload,
            interface_types=INTERFACE_TYPES,
            error=exc.message,
        ), exc.status_code

    return (
        f'<div id="device-interfaces-section" hx-swap-oob="true">'
        f"{_interfaces_section(device_id)}</div>",
        200,
        {"HX-Trigger": "interface-saved"},
    )


@devices_bp.get("/<int:device_id>/interfaces/<int:interface_id>/edit")
def edit_interface_form(device_id: int, interface_id: int):
    try:
        device = api_get(f"/devices/{device_id}")
        interface = api_get(f"/interfaces/{interface_id}")
    except ApiError as exc:
        return (
            f'<div class="modal-header"><h5 class="modal-title">Not found</h5>'
            f'<button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>'
            f'<div class="modal-body"><div class="alert alert-danger mb-0">'
            f"{exc.message}</div></div>",
            exc.status_code,
        )

    return render_template(
        "devices/_interface_form.html",
        device=device,
        interface=interface,
        interface_types=INTERFACE_TYPES,
        error=None,
    )


@devices_bp.put("/<int:device_id>/interfaces/<int:interface_id>")
def update_interface(device_id: int, interface_id: int):
    payload = {
        "name": request.form.get("name", "").strip(),
        "interface_type": request.form.get("interface_type") or None,
        "mac_address": request.form.get("mac_address", "").strip() or None,
        "speed": request.form.get("speed", type=int),
        "mtu": request.form.get("mtu", type=int),
        "description": request.form.get("description", "").strip() or None,
        "is_active": request.form.get("is_active") == "on",
    }

    try:
        api_put(f"/interfaces/{interface_id}", payload)
    except ApiError as exc:
        device = api_get(f"/devices/{device_id}")
        payload["id"] = interface_id
        return render_template(
            "devices/_interface_form.html",
            device=device,
            interface=payload,
            interface_types=INTERFACE_TYPES,
            error=exc.message,
        ), exc.status_code

    return (
        f'<div id="device-interfaces-section" hx-swap-oob="true">'
        f"{_interfaces_section(device_id)}</div>",
        200,
        {"HX-Trigger": "interface-saved"},
    )


@devices_bp.delete("/<int:device_id>/interfaces/<int:interface_id>")
def delete_interface(device_id: int, interface_id: int):
    try:
        api_delete(f"/interfaces/{interface_id}")
    except ApiError as exc:
        return (
            f'<div class="alert alert-danger py-2 mb-2">{exc.message}</div>',
            exc.status_code,
        )

    return _interfaces_section(device_id)


# --- IP Addresses CRUD (device-scoped) ---


def _ip_addresses_section(device_id: int) -> str:
    context = _device_details_context(device_id)
    return render_template(
        "devices/_ip_addresses_section.html",
        device=context["device"],
        ip_addresses=context["ip_addresses"],
    )


@devices_bp.get("/<int:device_id>/ip-addresses/new")
def new_ip_address_form(device_id: int):
    device = api_get(f"/devices/{device_id}")
    interfaces = device_interfaces(api_get("/interfaces"), device_id)
    return render_template(
        "devices/_ip_address_form.html",
        device=device,
        ip_address=None,
        interfaces=interfaces,
        error=None,
    )


@devices_bp.post("/<int:device_id>/ip-addresses")
def create_ip_address(device_id: int):
    payload = {
        "interface_id": request.form.get("interface_id", type=int),
        "address": request.form.get("address", "").strip(),
        "version": request.form.get("version", type=int),
        "is_primary": request.form.get("is_primary") == "on",
        "description": request.form.get("description", "").strip() or None,
    }

    try:
        api_post("/ip-addresses", payload)
    except ApiError as exc:
        device = api_get(f"/devices/{device_id}")
        interfaces = device_interfaces(api_get("/interfaces"), device_id)
        return render_template(
            "devices/_ip_address_form.html",
            device=device,
            ip_address=payload,
            interfaces=interfaces,
            error=exc.message,
        ), exc.status_code

    return (
        f'<div id="device-ip-addresses-section" hx-swap-oob="true">'
        f"{_ip_addresses_section(device_id)}</div>",
        200,
        {"HX-Trigger": "ip-address-saved"},
    )


@devices_bp.get("/<int:device_id>/ip-addresses/<int:ip_address_id>/edit")
def edit_ip_address_form(device_id: int, ip_address_id: int):
    try:
        device = api_get(f"/devices/{device_id}")
        ip_address = api_get(f"/ip-addresses/{ip_address_id}")
    except ApiError as exc:
        return (
            f'<div class="modal-header"><h5 class="modal-title">Not found</h5>'
            f'<button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>'
            f'<div class="modal-body"><div class="alert alert-danger mb-0">'
            f"{exc.message}</div></div>",
            exc.status_code,
        )

    interfaces = device_interfaces(api_get("/interfaces"), device_id)
    return render_template(
        "devices/_ip_address_form.html",
        device=device,
        ip_address=ip_address,
        interfaces=interfaces,
        error=None,
    )


@devices_bp.put("/<int:device_id>/ip-addresses/<int:ip_address_id>")
def update_ip_address(device_id: int, ip_address_id: int):
    payload = {
        "interface_id": request.form.get("interface_id", type=int),
        "address": request.form.get("address", "").strip(),
        "version": request.form.get("version", type=int),
        "is_primary": request.form.get("is_primary") == "on",
        "description": request.form.get("description", "").strip() or None,
    }

    try:
        api_put(f"/ip-addresses/{ip_address_id}", payload)
    except ApiError as exc:
        device = api_get(f"/devices/{device_id}")
        interfaces = device_interfaces(api_get("/interfaces"), device_id)
        payload["id"] = ip_address_id
        return render_template(
            "devices/_ip_address_form.html",
            device=device,
            ip_address=payload,
            interfaces=interfaces,
            error=exc.message,
        ), exc.status_code

    return (
        f'<div id="device-ip-addresses-section" hx-swap-oob="true">'
        f"{_ip_addresses_section(device_id)}</div>",
        200,
        {"HX-Trigger": "ip-address-saved"},
    )


@devices_bp.delete("/<int:device_id>/ip-addresses/<int:ip_address_id>")
def delete_ip_address(device_id: int, ip_address_id: int):
    try:
        api_delete(f"/ip-addresses/{ip_address_id}")
    except ApiError as exc:
        return (
            f'<div class="alert alert-danger py-2 mb-2">{exc.message}</div>',
            exc.status_code,
        )

    return _ip_addresses_section(device_id)


# --- Ports CRUD (device-scoped) ---


def _ports_section(device_id: int) -> str:
    context = _device_details_context(device_id)
    return render_template(
        "devices/_ports_section.html",
        device=context["device"],
        ports=context["ports"],
    )


@devices_bp.get("/<int:device_id>/ports/new")
def new_port_form(device_id: int):
    device = api_get(f"/devices/{device_id}")
    return render_template(
        "devices/_port_form.html",
        device=device,
        port=None,
        port_statuses=PORT_STATUSES,
        web_schemes=WEB_SCHEMES,
        error=None,
    )


@devices_bp.post("/<int:device_id>/ports")
def create_port(device_id: int):
    payload = {
        "device_id": device_id,
        "port_number": request.form.get("port_number", type=int),
        "protocol": request.form.get("protocol") or None,
        "status": request.form.get("status", "open"),
        "display_name": request.form.get("display_name", "").strip() or None,
        "web_scheme": request.form.get("web_scheme") or None,
        "description": request.form.get("description", "").strip() or None,
    }

    try:
        api_post("/ports", payload)
    except ApiError as exc:
        device = api_get(f"/devices/{device_id}")
        return render_template(
            "devices/_port_form.html",
            device=device,
            port=payload,
            port_statuses=PORT_STATUSES,
            web_schemes=WEB_SCHEMES,
            error=exc.message,
        ), exc.status_code

    return (
        f'<div id="device-ports-section" hx-swap-oob="true">'
        f"{_ports_section(device_id)}</div>",
        200,
        {"HX-Trigger": "port-saved"},
    )


@devices_bp.get("/<int:device_id>/ports/<int:port_id>/edit")
def edit_port_form(device_id: int, port_id: int):
    try:
        device = api_get(f"/devices/{device_id}")
        port = api_get(f"/ports/{port_id}")
    except ApiError as exc:
        return (
            f'<div class="modal-header"><h5 class="modal-title">Not found</h5>'
            f'<button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>'
            f'<div class="modal-body"><div class="alert alert-danger mb-0">'
            f"{exc.message}</div></div>",
            exc.status_code,
        )

    return render_template(
        "devices/_port_form.html",
        device=device,
        port=port,
        port_statuses=PORT_STATUSES,
        web_schemes=WEB_SCHEMES,
        error=None,
    )


@devices_bp.put("/<int:device_id>/ports/<int:port_id>")
def update_port(device_id: int, port_id: int):
    payload = {
        "port_number": request.form.get("port_number", type=int),
        "protocol": request.form.get("protocol") or None,
        "status": request.form.get("status", "open"),
        "display_name": request.form.get("display_name", "").strip() or None,
        "web_scheme": request.form.get("web_scheme") or None,
        "description": request.form.get("description", "").strip() or None,
    }

    try:
        api_put(f"/ports/{port_id}", payload)
    except ApiError as exc:
        device = api_get(f"/devices/{device_id}")
        payload["id"] = port_id
        return render_template(
            "devices/_port_form.html",
            device=device,
            port=payload,
            port_statuses=PORT_STATUSES,
            web_schemes=WEB_SCHEMES,
            error=exc.message,
        ), exc.status_code

    return (
        f'<div id="device-ports-section" hx-swap-oob="true">'
        f"{_ports_section(device_id)}</div>",
        200,
        {"HX-Trigger": "port-saved"},
    )


@devices_bp.delete("/<int:device_id>/ports/<int:port_id>")
def delete_port(device_id: int, port_id: int):
    try:
        api_delete(f"/ports/{port_id}")
    except ApiError as exc:
        return (
            f'<div class="alert alert-danger py-2 mb-2">{exc.message}</div>',
            exc.status_code,
        )

    return _ports_section(device_id)
