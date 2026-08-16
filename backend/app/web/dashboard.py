from __future__ import annotations

from flask import Blueprint, render_template

from .api_client import api_get
from .helpers import device_display_name, index_by_id

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/dashboard")
def dashboard():
    sites = api_get("/sites")
    networks = api_get("/networks")
    devices = api_get("/devices")
    ports = api_get("/ports")
    connections = api_get("/connections")
    interfaces = api_get("/interfaces")
    ip_addresses = api_get("/ip-addresses")

    networks_by_id = index_by_id(networks)

    active_devices = [d for d in devices if d.get("is_active")]
    inactive_devices = [d for d in devices if not d.get("is_active")]

    recent_devices = sorted(
        devices,
        key=lambda d: d.get("updated_at") or "",
        reverse=True,
    )[:5]

    linked_device_ids = {
        device_id
        for connection in connections
        for device_id in (
            connection.get("source_device_id"),
            connection.get("target_device_id"),
        )
        if device_id is not None
    }
    devices_without_links = [
        d for d in devices if d["id"] not in linked_device_ids
    ]

    for device in recent_devices + inactive_devices + devices_without_links:
        network = networks_by_id.get(device.get("network_id"))
        device["network_name"] = network["name"] if network else "—"
        device["display"] = device_display_name(device)

    stats = {
        "sites": len(sites),
        "networks": len(networks),
        "devices": len(devices),
        "active_devices": len(active_devices),
        "inactive_devices": len(inactive_devices),
        "interfaces": len(interfaces),
        "ip_addresses": len(ip_addresses),
        "ports": len(ports),
        "connections": len(connections),
    }

    return render_template(
        "dashboard.html",
        stats=stats,
        recent_devices=recent_devices,
        inactive_devices=inactive_devices[:5],
        devices_without_links=devices_without_links[:5],
        devices_without_links_total=len(devices_without_links),
        active_page="dashboard",
    )
