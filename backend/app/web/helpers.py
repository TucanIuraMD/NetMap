"""Shared helpers for the Web UI layer.

NOTE: ``GET /api/v1/devices`` now implements search/filter/sort/
pagination server-side (see ``api/v1/devices.py``), so the Web UI
passes those query parameters through and only enriches the returned
page. The in-memory helpers below are kept for other collections and
for UI-side fallbacks.
"""

from __future__ import annotations

from typing import Any


def index_by_id(items: list[dict]) -> dict[int, dict]:
    return {item["id"]: item for item in items}


def device_display_name(device: dict) -> str:
    return device.get("display_name") or device.get("name") or "—"


GENERIC_INTERFACE_NAMES = {"", "discovered", "unknown", "iface", "interface", "eth"}


def interface_display_label(interface: dict, primary_ip: str | None = None) -> str:
    """Human-readable, unique label for an interface.

    Uses the real interface name when available; falls back to a stable
    unique signature (``iface {id}`` or ``iface {id} ({ip})``) for
    generic discovery placeholders like "discovered".
    """
    name = (interface.get("name") or "").strip()

    if name.lower() not in GENERIC_INTERFACE_NAMES:
        return name

    if primary_ip:
        return f"iface {interface.get('id')} ({primary_ip})"

    return f"iface {interface.get('id')}"


# Well-known service ports (port, protocol) -> display name. This is a
# presentation-layer fallback only: a port's own ``display_name`` (or the
# service attached to it) always wins. Used when the UI shows a port and
# there is no human-readable name stored for it.
STANDARD_PORT_NAMES: dict[tuple[int, str], str] = {
    # Web & base infrastructure
    (53, "tcp"): "DNS",
    (53, "udp"): "DNS",
    (67, "udp"): "DHCP",
    (68, "udp"): "DHCP",
    (80, "tcp"): "HTTP",
    (123, "udp"): "NTP",
    (443, "tcp"): "HTTPS",
    # Remote access & file transfer
    (20, "tcp"): "FTP",
    (21, "tcp"): "FTP",
    (22, "tcp"): "SSH / SFTP",
    (23, "tcp"): "Telnet",
    (69, "udp"): "TFTP",
    (3389, "tcp"): "RDP",
    (3389, "udp"): "RDP",
    # Email
    (25, "tcp"): "SMTP",
    (110, "tcp"): "POP3",
    (143, "tcp"): "IMAP",
    (465, "tcp"): "SMTPS",
    (587, "tcp"): "SMTP (Submission)",
    (993, "tcp"): "IMAPS",
    (995, "tcp"): "POP3S",
    # Databases
    (1433, "tcp"): "Microsoft SQL Server",
    (1521, "tcp"): "Oracle Database",
    (3306, "tcp"): "MySQL / MariaDB",
    (5432, "tcp"): "PostgreSQL",
    (6379, "tcp"): "Redis",
    (27017, "tcp"): "MongoDB",
    # Network management & monitoring
    (161, "udp"): "SNMP",
    (162, "udp"): "SNMP",
    (389, "tcp"): "LDAP",
    (389, "udp"): "LDAP",
    (445, "tcp"): "SMB",
    (636, "tcp"): "LDAPS",
}


def port_service_name(port: dict) -> str | None:
    """Human-readable service name for a port.

    Returns the port's own ``display_name`` when present, otherwise a
    standard name from :data:`STANDARD_PORT_NAMES`. Returns ``None`` when
    neither is available. Never writes to the database.
    """
    display_name = (port.get("display_name") or "").strip()

    if display_name:
        return display_name

    protocol = (port.get("protocol") or "").strip().lower()
    return STANDARD_PORT_NAMES.get((port.get("port_number"), protocol))


def filter_devices(
    devices: list[dict],
    *,
    search: str = "",
    network_id: str = "",
    device_type: str = "",
    status: str = "",
    links: str = "",
) -> list[dict]:
    result = devices

    if search:
        needle = search.strip().lower()
        result = [
            d for d in result
            if needle in (d.get("name") or "").lower()
            or needle in (d.get("display_name") or "").lower()
            or needle in (d.get("hostname") or "").lower()
        ]

    if network_id:
        result = [
            d for d in result
            if str(d.get("network_id")) == str(network_id)
        ]

    if device_type:
        result = [
            d for d in result
            if (d.get("device_type") or "") == device_type
        ]

    if status == "active":
        result = [d for d in result if d.get("is_active")]
    elif status == "inactive":
        result = [d for d in result if not d.get("is_active")]

    if links == "with":
        result = [d for d in result if (d.get("connections_count") or 0) > 0]
    elif links == "without":
        result = [d for d in result if not d.get("connections_count")]

    return result


def sort_devices(devices: list[dict], sort: str = "") -> list[dict]:
    if not sort:
        return devices

    reverse = sort.startswith("-")
    key = sort.lstrip("-")

    sortable = {"name", "display_name", "hostname", "device_type"}

    if key not in sortable:
        return devices

    return sorted(
        devices,
        key=lambda d: (d.get(key) or "").lower(),
        reverse=reverse,
    )


def paginate(
    items: list[Any],
    page: int = 1,
    page_size: int = 50,
) -> dict:
    page = max(page, 1)
    page_size = max(min(page_size, 500), 1)

    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "items": items[start:end],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": max((total + page_size - 1) // page_size, 1),
    }


def device_type_options(devices: list[dict]) -> list[str]:
    types = {d.get("device_type") for d in devices if d.get("device_type")}
    return sorted(types)


def device_ports(ports: list[dict], device_id: int) -> list[dict]:
    return [p for p in ports if p.get("device_id") == device_id]


def device_interfaces(interfaces: list[dict], device_id: int) -> list[dict]:
    return [i for i in interfaces if i.get("device_id") == device_id]


def device_ip_addresses(
    ip_addresses: list[dict],
    interfaces: list[dict],
) -> list[dict]:
    interface_ids = {i["id"] for i in interfaces}
    return [
        ip for ip in ip_addresses
        if ip.get("interface_id") in interface_ids
    ]


def device_connections(
    connections: list[dict],
    device_id: int,
) -> list[dict]:
    return [
        c for c in connections
        if c.get("source_device_id") == device_id
        or c.get("target_device_id") == device_id
    ]
