"""Shared helpers for the Web UI layer.

NOTE (backend gap): docs/03_API.md advertises search/filter/sort/
pagination on list endpoints, but the current implementation of
``GET /api/v1/devices`` (and other list endpoints) ignores query
parameters entirely and always returns the full collection.

Until that is implemented in the API, filtering/sorting/pagination
for the UI happens here, in-memory, at the UI layer. This is a
deliberate, documented workaround — not a silent reinvention of the
API contract. See docs/UI_STATUS.md.
"""

from __future__ import annotations

from typing import Any


def index_by_id(items: list[dict]) -> dict[int, dict]:
    return {item["id"]: item for item in items}


def device_display_name(device: dict) -> str:
    return device.get("display_name") or device.get("name") or "—"


def filter_devices(
    devices: list[dict],
    *,
    search: str = "",
    network_id: str = "",
    device_type: str = "",
    status: str = "",
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
