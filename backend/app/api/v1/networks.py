from flask import Blueprint, jsonify, request

from ...extensions import db
from ...models.network import Network
from ...models.site import Site


networks_bp = Blueprint("networks", __name__, url_prefix="/networks")


def network_to_dict(network: Network) -> dict:
    return {
        "id": network.id,
        "site_id": network.site_id,
        "name": network.name,
        "cidr": network.cidr,
        "description": network.description,
        "is_active": network.is_active,
        "created_at": network.created_at.isoformat()
        if network.created_at else None,
        "updated_at": network.updated_at.isoformat()
        if network.updated_at else None,
    }


@networks_bp.get("")
def list_networks():
    networks = Network.query.order_by(Network.id).all()
    return jsonify([network_to_dict(network) for network in networks])


@networks_bp.get("/<int:network_id>")
def get_network(network_id: int):
    network = db.session.get(Network, network_id)

    if network is None:
        return jsonify({"error": "Network not found"}), 404

    return jsonify(network_to_dict(network))


@networks_bp.post("")
def create_network():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "JSON body is required"}), 400

    site_id = data.get("site_id")
    name = data.get("name")
    cidr = data.get("cidr")

    if site_id is None:
        return jsonify({"error": "site_id is required"}), 400

    if not name:
        return jsonify({"error": "name is required"}), 400

    if not cidr:
        return jsonify({"error": "cidr is required"}), 400

    site = db.session.get(Site, site_id)

    if site is None:
        return jsonify({"error": "Site not found"}), 404

    if Network.query.filter_by(site_id=site_id, name=name).first():
        return jsonify(
            {"error": "Network with this name already exists for this site"}
        ), 409

    network = Network(
        site_id=site_id,
        name=name,
        cidr=cidr,
        description=data.get("description"),
        is_active=data.get("is_active", True),
    )

    db.session.add(network)
    db.session.commit()

    return jsonify(network_to_dict(network)), 201


@networks_bp.put("/<int:network_id>")
def update_network(network_id: int):
    network = db.session.get(Network, network_id)

    if network is None:
        return jsonify({"error": "Network not found"}), 404

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "JSON body is required"}), 400

    if "site_id" in data:
        site_id = data["site_id"]

        site = db.session.get(Site, site_id)

        if site is None:
            return jsonify({"error": "Site not found"}), 404

        network.site_id = site_id

    if "name" in data:
        name = data["name"]

        if not name:
            return jsonify({"error": "name cannot be empty"}), 400

        existing = Network.query.filter(
            Network.site_id == network.site_id,
            Network.name == name,
            Network.id != network_id,
        ).first()

        if existing:
            return jsonify(
                {"error": "Network with this name already exists for this site"}
            ), 409

        network.name = name

    if "cidr" in data:
        cidr = data["cidr"]

        if not cidr:
            return jsonify({"error": "cidr cannot be empty"}), 400

        network.cidr = cidr

    if "description" in data:
        network.description = data["description"]

    if "is_active" in data:
        network.is_active = data["is_active"]

    db.session.commit()

    return jsonify(network_to_dict(network))


@networks_bp.delete("/<int:network_id>")
def delete_network(network_id: int):
    network = db.session.get(Network, network_id)

    if network is None:
        return jsonify({"error": "Network not found"}), 404

    db.session.delete(network)
    db.session.commit()

    return "", 204
