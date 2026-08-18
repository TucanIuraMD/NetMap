from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import func, or_, select

from ...extensions import db
from ...models.connection import Connection
from ...models.device import Device
from ...models.network import Network
from ...services.port_scanner import (
    NoIpAddressError,
    PortScanConflictError,
)


devices_bp = Blueprint("devices", __name__, url_prefix="/devices")

DEVICE_SORT_COLUMNS = {
    "id": Device.id,
    "name": Device.name,
    "display_name": Device.display_name,
    "hostname": Device.hostname,
    "device_type": Device.device_type,
}


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


def _device_has_connection():
    """Correlated EXISTS for any connection touching a Device."""
    return (
        select(Connection.id)
        .where(
            or_(
                Connection.source_device_id == Device.id,
                Connection.target_device_id == Device.id,
            )
        )
        .exists()
    )


def _paginate(query, page: int, per_page: int) -> dict:
    page = max(page, 1)
    per_page = max(min(per_page, 500), 1)

    total = query.count()
    total_pages = max((total + per_page - 1) // per_page, 1)
    items = (
        query.offset((page - 1) * per_page).limit(per_page).all()
    )

    return {
        "items": [device_to_dict(device) for device in items],
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
    }


@devices_bp.get("")
def list_devices():
    args = request.args

    # Backward-compatible fast path: no query parameters at all means
    # "return everything", exactly as before.
    if not args:
        devices = Device.query.order_by(Device.id).all()
        return jsonify([device_to_dict(device) for device in devices])

    query = Device.query

    search = args.get("search", "").strip()
    if search:
        needle = f"%{search}%"
        query = query.filter(
            or_(
                Device.name.ilike(needle),
                Device.display_name.ilike(needle),
                Device.hostname.ilike(needle),
            )
        )

    network_id = args.get("network_id", "").strip()
    if network_id:
        try:
            query = query.filter(Device.network_id == int(network_id))
        except ValueError:
            pass

    device_type = args.get("device_type", "").strip()
    if device_type:
        query = query.filter(Device.device_type == device_type)

    status = args.get("status", "").strip()
    if status == "active":
        query = query.filter(Device.is_active.is_(True))
    elif status == "inactive":
        query = query.filter(Device.is_active.is_(False))

    links = args.get("links", "").strip()
    if links == "with":
        query = query.filter(_device_has_connection())
    elif links == "without":
        query = query.filter(~_device_has_connection())

    sort = args.get("sort", "").strip()
    field = sort.lstrip("-")
    reverse = sort.startswith("-")
    order = args.get("order", "").strip().lower()
    if order in ("asc", "desc"):
        reverse = order == "desc"

    column = DEVICE_SORT_COLUMNS.get(field)
    if column is not None:
        ordered = func.lower(column)
        query = query.order_by(
            ordered.desc() if reverse else ordered.asc(),
            Device.id,
        )
    else:
        query = query.order_by(Device.id)

    page = args.get("page", 1, type=int)
    per_page = args.get("per_page", type=int)
    if per_page is None:
        per_page = args.get("page_size", 50, type=int)

    return jsonify(_paginate(query, page, per_page))


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
        display_name=data.get("display_name"),
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


@devices_bp.post("/<int:device_id>/ports/scan")
def scan_device_ports(device_id: int):
    """Scan a single device's well-known TCP ports and sync results."""
    device = db.session.get(Device, device_id)

    if device is None:
        return jsonify({"error": "Device not found"}), 404

    service = current_app.extensions["port_scanner_service"]

    try:
        result = service.scan_device(device)
    except NoIpAddressError as exc:
        return jsonify({"error": str(exc)}), 400
    except PortScanConflictError as exc:
        return jsonify({"error": str(exc)}), 409

    return jsonify(
        {
            "device_id": result.device_id,
            "ip_address": result.ip_address,
            "ports_scanned": result.ports_scanned,
            "open_ports": result.open_ports,
            "elapsed_ms": result.elapsed_ms,
            "created": result.created,
            "updated": result.updated,
        }
    )
