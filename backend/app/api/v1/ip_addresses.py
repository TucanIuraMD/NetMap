from flask import Blueprint, jsonify, request

from ...extensions import db
from ...models.interface import Interface
from ...models.ip_address import IPAddress
from .validation import validate_ip_address


ip_addresses_bp = Blueprint(
    "ip_addresses",
    __name__,
    url_prefix="/ip-addresses",
)


def ip_address_to_dict(ip_address: IPAddress) -> dict:
    return {
        "id": ip_address.id,
        "interface_id": ip_address.interface_id,
        "address": ip_address.address,
        "version": ip_address.version,
        "is_primary": ip_address.is_primary,
        "description": ip_address.description,
        "created_at": (
            ip_address.created_at.isoformat()
            if ip_address.created_at else None
        ),
        "updated_at": (
            ip_address.updated_at.isoformat()
            if ip_address.updated_at else None
        ),
    }


@ip_addresses_bp.get("")
def list_ip_addresses():
    addresses = IPAddress.query.order_by(IPAddress.id).all()
    return jsonify([
        ip_address_to_dict(address)
        for address in addresses
    ])


@ip_addresses_bp.get("/<int:ip_address_id>")
def get_ip_address(ip_address_id: int):
    ip_address = db.session.get(IPAddress, ip_address_id)

    if ip_address is None:
        return jsonify({"error": "IP address not found"}), 404

    return jsonify(ip_address_to_dict(ip_address))


@ip_addresses_bp.post("")
def create_ip_address():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "JSON body is required"}), 400

    interface_id = data.get("interface_id")
    address = data.get("address")
    version = data.get("version")

    if interface_id is None:
        return jsonify({"error": "interface_id is required"}), 400

    if not address:
        return jsonify({"error": "address is required"}), 400

    if version not in (4, 6):
        return jsonify({
            "error": "version must be 4 or 6"
        }), 400

    interface = db.session.get(Interface, interface_id)

    if interface is None:
        return jsonify({"error": "Interface not found"}), 404

    address, error = validate_ip_address(address, version)
    if error:
        return jsonify({"error": error}), 400

    if IPAddress.query.filter_by(
        interface_id=interface_id,
        address=address,
    ).first():
        return jsonify({
            "error": "IP address already exists for this interface"
        }), 409

    ip_address = IPAddress(
        interface_id=interface_id,
        address=address,
        version=version,
        is_primary=data.get("is_primary", False),
        description=data.get("description"),
    )

    db.session.add(ip_address)
    db.session.commit()

    return jsonify(ip_address_to_dict(ip_address)), 201


@ip_addresses_bp.put("/<int:ip_address_id>")
def update_ip_address(ip_address_id: int):
    ip_address = db.session.get(IPAddress, ip_address_id)

    if ip_address is None:
        return jsonify({"error": "IP address not found"}), 404

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "JSON body is required"}), 400

    if "interface_id" in data:
        interface_id = data["interface_id"]

        interface = db.session.get(Interface, interface_id)

        if interface is None:
            return jsonify({"error": "Interface not found"}), 404

        ip_address.interface_id = interface_id

    if "address" in data:
        address, error = validate_ip_address(
            data["address"],
            ip_address.version,
        )
        if error:
            return jsonify({"error": error}), 400

        existing = IPAddress.query.filter(
            IPAddress.interface_id == ip_address.interface_id,
            IPAddress.address == address,
            IPAddress.id != ip_address_id,
        ).first()

        if existing:
            return jsonify({
                "error": "IP address already exists for this interface"
            }), 409

        ip_address.address = address

    if "version" in data:
        version = data["version"]

        if version not in (4, 6):
            return jsonify({
                "error": "version must be 4 or 6"
            }), 400

        address, error = validate_ip_address(
            ip_address.address,
            version,
        )
        if error:
            return jsonify({"error": error}), 400

        ip_address.version = version

    if "is_primary" in data:
        ip_address.is_primary = data["is_primary"]

    if "description" in data:
        ip_address.description = data["description"]

    db.session.commit()

    return jsonify(ip_address_to_dict(ip_address))


@ip_addresses_bp.delete("/<int:ip_address_id>")
def delete_ip_address(ip_address_id: int):
    ip_address = db.session.get(IPAddress, ip_address_id)

    if ip_address is None:
        return jsonify({"error": "IP address not found"}), 404

    db.session.delete(ip_address)
    db.session.commit()

    return "", 204
