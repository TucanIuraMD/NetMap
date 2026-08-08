from flask import Blueprint, jsonify, request

from ...extensions import db
from ...models.device import Device
from ...models.interface import Interface


interfaces_bp = Blueprint(
    "interfaces",
    __name__,
    url_prefix="/interfaces",
)


def interface_to_dict(interface: Interface) -> dict:
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
        "created_at": (
            interface.created_at.isoformat()
            if interface.created_at else None
        ),
        "updated_at": (
            interface.updated_at.isoformat()
            if interface.updated_at else None
        ),
    }


@interfaces_bp.get("")
def list_interfaces():
    interfaces = Interface.query.order_by(Interface.id).all()
    return jsonify(
        [interface_to_dict(interface) for interface in interfaces]
    )


@interfaces_bp.get("/<int:interface_id>")
def get_interface(interface_id: int):
    interface = db.session.get(Interface, interface_id)

    if interface is None:
        return jsonify({"error": "Interface not found"}), 404

    return jsonify(interface_to_dict(interface))


@interfaces_bp.post("")
def create_interface():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "JSON body is required"}), 400

    device_id = data.get("device_id")
    name = data.get("name")

    if device_id is None:
        return jsonify({"error": "device_id is required"}), 400

    if not name:
        return jsonify({"error": "name is required"}), 400

    device = db.session.get(Device, device_id)

    if device is None:
        return jsonify({"error": "Device not found"}), 404

    if Interface.query.filter_by(
        device_id=device_id,
        name=name,
    ).first():
        return jsonify({
            "error": "Interface with this name already exists for this device"
        }), 409

    interface = Interface(
        device_id=device_id,
        name=name,
        mac_address=data.get("mac_address"),
        speed=data.get("speed"),
        mtu=data.get("mtu"),
        interface_type=data.get("interface_type"),
        description=data.get("description"),
        is_active=data.get("is_active", True),
    )

    db.session.add(interface)
    db.session.commit()

    return jsonify(interface_to_dict(interface)), 201


@interfaces_bp.put("/<int:interface_id>")
def update_interface(interface_id: int):
    interface = db.session.get(Interface, interface_id)

    if interface is None:
        return jsonify({"error": "Interface not found"}), 404

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "JSON body is required"}), 400

    if "device_id" in data:
        device_id = data["device_id"]

        device = db.session.get(Device, device_id)

        if device is None:
            return jsonify({"error": "Device not found"}), 404

        interface.device_id = device_id

    if "name" in data:
        name = data["name"]

        if not name:
            return jsonify({"error": "name cannot be empty"}), 400

        existing = Interface.query.filter(
            Interface.device_id == interface.device_id,
            Interface.name == name,
            Interface.id != interface_id,
        ).first()

        if existing:
            return jsonify({
                "error": (
                    "Interface with this name already exists "
                    "for this device"
                )
            }), 409

        interface.name = name

    if "mac_address" in data:
        interface.mac_address = data["mac_address"]

    if "speed" in data:
        interface.speed = data["speed"]

    if "mtu" in data:
        interface.mtu = data["mtu"]

    if "interface_type" in data:
        interface.interface_type = data["interface_type"]

    if "description" in data:
        interface.description = data["description"]

    if "is_active" in data:
        interface.is_active = data["is_active"]

    db.session.commit()

    return jsonify(interface_to_dict(interface))


@interfaces_bp.delete("/<int:interface_id>")
def delete_interface(interface_id: int):
    interface = db.session.get(Interface, interface_id)

    if interface is None:
        return jsonify({"error": "Interface not found"}), 404

    db.session.delete(interface)
    db.session.commit()

    return "", 204
