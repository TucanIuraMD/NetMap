from __future__ import annotations

from app.models.connection import Connection
from app.models.device import Device
from app.models.interface import Interface
from app.models.ip_address import IPAddress
from app.models.port import Port

# Interface names treated as generic/uninformative by the UI (see
# static/js/topology.js); they are skipped when building edge labels.
GENERIC_IFACE_NAMES = {"discovered", "unknown", "iface", "interface", "eth"}


def _iso(value):
    return value.isoformat() if value else None


def _device_to_dict(device: Device) -> dict:
    return {
        "id": device.id,
        "network_id": device.network_id,
        "name": device.name,
        "display_name": device.display_name,
        "hostname": device.hostname,
        "device_type": device.device_type,
        "description": device.description,
        "is_active": device.is_active,
        "created_at": _iso(device.created_at),
        "updated_at": _iso(device.updated_at),
    }


def _ip_address_to_dict(ip_address: IPAddress) -> dict:
    return {
        "id": ip_address.id,
        "interface_id": ip_address.interface_id,
        "address": ip_address.address,
        "version": ip_address.version,
        "is_primary": ip_address.is_primary,
        "description": ip_address.description,
        "created_at": _iso(ip_address.created_at),
        "updated_at": _iso(ip_address.updated_at),
    }


def _interface_to_dict(interface: Interface) -> dict:
    return {
        "id": interface.id,
        "device_id": interface.device_id,
        "name": interface.name,
        "mac_address": interface.mac_address,
        "speed": interface.speed,
        "mtu": interface.mtu,
        "interface_type": interface.interface_type,
        "description": interface.description,
        "is_active": interface.is_active,
        "created_at": _iso(interface.created_at),
        "updated_at": _iso(interface.updated_at),
        "ip_addresses": [
            _ip_address_to_dict(ip_address)
            for ip_address in interface.ip_addresses
        ],
    }


def _port_to_dict(port: Port) -> dict:
    return {
        "id": port.id,
        "device_id": port.device_id,
        "service_id": port.service_id,
        "port_number": port.port_number,
        "protocol": port.protocol,
        "status": port.status,
        "display_name": port.display_name,
        "web_scheme": port.web_scheme,
        "description": port.description,
        "created_at": _iso(port.created_at),
        "updated_at": _iso(port.updated_at),
    }


def _connection_to_dict(connection: Connection) -> dict:
    return {
        "id": connection.id,
        "source_device_id": connection.source_device_id,
        "target_device_id": connection.target_device_id,
        "connection_type": connection.connection_type,
        "source_port_id": connection.source_port_id,
        "target_port_id": connection.target_port_id,
        "source_interface_id": connection.source_interface_id,
        "target_interface_id": connection.target_interface_id,
        "description": connection.description,
        "is_active": connection.is_active,
        "created_at": _iso(connection.created_at),
        "updated_at": _iso(connection.updated_at),
    }


def _interface_label(interface: Interface | None) -> str | None:
    if interface is None:
        return None

    name = (interface.name or "").strip()

    if name and name.lower() not in GENERIC_IFACE_NAMES:
        return name

    return f"iface {interface.id}"


def _edge_label(
    connection: Connection,
    source_device_id: int,
    target_device_id: int,
) -> str | None:
    source_iface = connection.source_interface
    target_iface = connection.target_interface

    if (
        source_iface is not None
        and source_iface.device_id != source_device_id
    ):
        source_iface = None

    if (
        target_iface is not None
        and target_iface.device_id != target_device_id
    ):
        target_iface = None

    source_label = _interface_label(source_iface)
    target_label = _interface_label(target_iface)

    if source_label and target_label:
        return f"{source_label} → {target_label}"

    if source_label:
        return f"{source_label} →"

    if target_label:
        return f"→ {target_label}"

    return None


class TopologyService:
    """Build the device/connection graph served by GET /api/v1/topology.

    Nodes are devices (with their interfaces, IP addresses and ports
    attached). Edges are derived strictly from the existing
    ``Connection`` records — no synthetic links are ever fabricated, and
    every connection maps to exactly one edge.
    """

    @staticmethod
    def build(
        network_id: int | None = None,
        device_type: str | None = None,
        status: str | None = None,
    ) -> dict:
        query = Device.query

        if network_id is not None:
            query = query.filter(Device.network_id == network_id)

        if device_type:
            query = query.filter(Device.device_type == device_type)

        if status == "active":
            query = query.filter(Device.is_active.is_(True))
        elif status == "inactive":
            query = query.filter(Device.is_active.is_(False))

        devices = query.order_by(Device.id).all()
        device_ids = {device.id for device in devices}

        connections = Connection.query.order_by(Connection.id).all()

        edges = []
        linked_ids = set()

        for connection in connections:
            source_device_id = connection.source_device_id
            target_device_id = connection.target_device_id

            # Only connections whose endpoints are part of the node set
            # produce edges, so every edge always references a visible
            # node. Source and target are guaranteed to differ by the
            # connections API.
            if (
                source_device_id not in device_ids
                or target_device_id not in device_ids
            ):
                continue

            linked_ids.add(source_device_id)
            linked_ids.add(target_device_id)

            edges.append({
                "data": {
                    "id": f"conn-{connection.id}",
                    "source": f"device-{source_device_id}",
                    "target": f"device-{target_device_id}",
                    "type": connection.connection_type,
                    "label": _edge_label(
                        connection,
                        source_device_id,
                        target_device_id,
                    ),
                    "connection": _connection_to_dict(connection),
                }
            })

        nodes = [
            {
                "data": {
                    "id": f"device-{device.id}",
                    "deviceId": device.id,
                    "label": device.display_name or device.name,
                    "isActive": device.is_active,
                    "linked": device.id in linked_ids,
                    "device": _device_to_dict(device),
                    "interfaces": [
                        _interface_to_dict(interface)
                        for interface in device.interfaces
                    ],
                    "ports": [
                        _port_to_dict(port)
                        for port in device.ports
                    ],
                }
            }
            for device in devices
        ]

        return {"nodes": nodes, "edges": edges}