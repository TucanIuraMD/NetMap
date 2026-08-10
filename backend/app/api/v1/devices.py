from flask import Blueprint, jsonify, request

from ...extensions import db
from ...models.device import Device
from ...models.network import Network


devices_bp = Blueprint("devices", __name__, url_prefix="/devices")


def device_to_dict(device: Device) -> dict:
    return {
        "id": device.id,
        "network_id": device.network_id,
        "name": device.name,
        "display_name": device.display_name,
        "hostname": device.hostname,
        "device_type": device.device_type,
        "description": device.description,
        "is_active": device.is_active,
        "created_at": (
            device.created_at.isoformat()
            if device.created_at else None
        ),
        "updated_at": (
            device.updated_at.isoformat()
            if device.updated_at else None
        ),
    }


@devices_bp.get("")
def list_devices():
    devices = Device.query.order_by(Device.id).all()
    return jsonify([device_to_dict(device) for device in devices])


@devices_bp.get("/<int:device_id>")
def get_device(device_id: int):
    device = db.session.get(Device, device_id)

    if device is None:
        return jsonify({"error": "Device not found"}), 404

    return jsonify(device_to_dict(device))


@devices_bp.post("")
def create_device():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "JSON body is required"}), 400

    network_id = data.get("network_id")
    name = data.get("name")

    display_name=data.get("display_name"),

    if network_id is None:
        return jsonify({"error": "network_id is required"}), 400

    if not name:
        return jsonify({"error": "name is required"}), 400

    network = db.session.get(Network, network_id)

    if network is None:
        return jsonify({"error": "Network not found"}), 404

    if Device.query.filter_by(
        network_id=network_id,
        name=name,
    ).first():
        return jsonify({
            "error": "Device with this name already exists for this network"
        }), 409

    device = Device(
        network_id=network_id,
        name=name,
        hostname=data.get("hostname"),
        device_type=data.get("device_type"),
        description=data.get("description"),
        is_active=data.get("is_active", True),
    )

    db.session.add(device)
    db.session.commit()

    return jsonify(device_to_dict(device)), 201


@devices_bp.put("/<int:device_id>")
def update_device(device_id: int):
    device = db.session.get(Device, device_id)

    if device is None:
        return jsonify({"error": "Device not found"}), 404

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "JSON body is required"}), 400

    if "network_id" in data:
        network_id = data["network_id"]

        network = db.session.get(Network, network_id)

        if network is None:
            return jsonify({"error": "Network not found"}), 404

        device.network_id = network_id

    if "display_name" in data:
        display_name = data["display_name"]

        if display_name is not None and not display_name.strip():
            return jsonify({
                "error": "display_name cannot be empty"
            }), 400

        device.display_name = display_name

    if "name" in data:
        name = data["name"]

        if not name:
            return jsonify({"error": "name cannot be empty"}), 400

        existing = Device.query.filter(
            Device.network_id == device.network_id,
            Device.name == name,
            Device.id != device_id,
        ).first()

        if existing:
            return jsonify({
                "error": "Device with this name already exists for this network"
            }), 409

        device.name = name

    if "hostname" in data:
        device.hostname = data["hostname"]

    if "device_type" in data:
        device.device_type = data["device_type"]

    if "description" in data:
        device.description = data["description"]

    if "is_active" in data:
        device.is_active = data["is_active"]

    db.session.commit()

    return jsonify(device_to_dict(device))


@devices_bp.delete("/<int:device_id>")
def delete_device(device_id: int):
    device = db.session.get(Device, device_id)

    if device is None:
        return jsonify({"error": "Device not found"}), 404

    db.session.delete(device)
    db.session.commit()

    return "", 204
