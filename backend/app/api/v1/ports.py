from flask import Blueprint, jsonify, request

from ...extensions import db
from ...models.device import Device
from ...models.port import Port
from ...models.service import Service
from .validation import (
    validate_port_number,
    validate_port_protocol,
    validate_port_status,
)


ports_bp = Blueprint(
    "ports",
    __name__,
    url_prefix="/ports",
)

def get_web_url(port: Port) -> str | None:
    if port.protocol.lower() != "tcp":
        return None

    if port.web_scheme not in {"http", "https"}:
        return None

    ip_address = None

    for interface in port.device.interfaces:
        primary = next(
            (
                ip
                for ip in interface.ip_addresses
                if ip.is_primary
            ),
            None,
        )

        if primary is not None:
            ip_address = primary.address
            break

    if ip_address is None:
        return None

    return f"{port.web_scheme}://{ip_address}:{port.port_number}"

def port_to_dict(port: Port) -> dict:
    return {
        "id": port.id,
        "device_id": port.device_id,
        "service_id": port.service_id,
        "port_number": port.port_number,
        "protocol": port.protocol,
        "status": port.status,
        "display_name": port.display_name,
        "web_scheme": port.web_scheme,
        "web_url": get_web_url(port),
        "description": port.description,
        "created_at": (
            port.created_at.isoformat()
            if port.created_at else None
        ),
        "updated_at": (
            port.updated_at.isoformat()
            if port.updated_at else None
        ),
    }


@ports_bp.get("")
def list_ports():
    ports = Port.query.order_by(Port.id).all()
    return jsonify([port_to_dict(port) for port in ports])


@ports_bp.get("/<int:port_id>")
def get_port(port_id: int):
    port = db.session.get(Port, port_id)

    if port is None:
        return jsonify({"error": "Port not found"}), 404

    return jsonify(port_to_dict(port))


@ports_bp.post("")
def create_port():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "JSON body is required"}), 400

    device_id = data.get("device_id")
    port_number = data.get("port_number")
    protocol = data.get("protocol")

    if device_id is None:
        return jsonify({"error": "device_id is required"}), 400

    if port_number is None:
        return jsonify({"error": "port_number is required"}), 400

    if not protocol:
        return jsonify({"error": "protocol is required"}), 400

    device = db.session.get(Device, device_id)

    if device is None:
        return jsonify({"error": "Device not found"}), 404

    port_number, error = validate_port_number(port_number)
    if error:
        return jsonify({"error": error}), 400

    protocol, error = validate_port_protocol(protocol)
    if error:
        return jsonify({"error": error}), 400

    status, error = validate_port_status(data.get("status", "open"))
    if error:
        return jsonify({"error": error}), 400

    service_id = data.get("service_id")

    if service_id is not None:
        service = db.session.get(Service, service_id)

        if service is None:
            return jsonify({"error": "Service not found"}), 404

    if Port.query.filter_by(
        device_id=device_id,
        port_number=port_number,
        protocol=protocol,
    ).first():
        return jsonify({
            "error": "Port already exists for this device"
        }), 409

    port = Port(
        device_id=device_id,
        service_id=service_id,
        port_number=port_number,
        protocol=protocol,
        status=status,
        display_name=data.get("display_name"),
        web_scheme=data.get("web_scheme"),
        description=data.get("description"),
    )

    db.session.add(port)
    db.session.commit()

    return jsonify(port_to_dict(port)), 201


@ports_bp.put("/<int:port_id>")
def update_port(port_id: int):
    port = db.session.get(Port, port_id)

    if port is None:
        return jsonify({"error": "Port not found"}), 404

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "JSON body is required"}), 400

    if "device_id" in data:
        device_id = data["device_id"]

        device = db.session.get(Device, device_id)

        if device is None:
            return jsonify({"error": "Device not found"}), 404

        port.device_id = device_id

    if "service_id" in data:
        service_id = data["service_id"]

        if service_id is not None:
            service = db.session.get(Service, service_id)

            if service is None:
                return jsonify({"error": "Service not found"}), 404

        port.service_id = service_id

    if "port_number" in data:
        port_number, error = validate_port_number(data["port_number"])
        if error:
            return jsonify({"error": error}), 400

        port.port_number = port_number

    if "protocol" in data:
        protocol, error = validate_port_protocol(data["protocol"])
        if error:
            return jsonify({"error": error}), 400

        port.protocol = protocol

    if "status" in data:
        status, error = validate_port_status(data["status"])
        if error:
            return jsonify({"error": error}), 400

        port.status = status

    if "display_name" in data:
        display_name = data["display_name"]

        if display_name is not None and not display_name.strip():
            return jsonify({
                "error": "display_name cannot be empty"
            }), 400

        port.display_name = display_name

    if "web_scheme" in data:
        web_scheme = data["web_scheme"]

        if web_scheme not in {None, "http", "https"}:
            return jsonify({
                "error": "web_scheme must be http, https, or null"
            }), 400

        port.web_scheme = web_scheme

    if "description" in data:
        port.description = data["description"]

    existing = Port.query.filter(
        Port.device_id == port.device_id,
        Port.port_number == port.port_number,
        Port.protocol == port.protocol,
        Port.id != port_id,
    ).first()

    if existing:
        return jsonify({
            "error": "Port already exists for this device"
        }), 409

    db.session.commit()

    return jsonify(port_to_dict(port))


@ports_bp.delete("/<int:port_id>")
def delete_port(port_id: int):
    port = db.session.get(Port, port_id)

    if port is None:
        return jsonify({"error": "Port not found"}), 404

    db.session.delete(port)
    db.session.commit()

    return "", 204
