from flask import Blueprint, jsonify, request

from ...extensions import db
from ...models.service import Service


services_bp = Blueprint(
    "services",
    __name__,
    url_prefix="/services",
)


def service_to_dict(service: Service) -> dict:
    return {
        "id": service.id,
        "name": service.name,
        "description": service.description,
        "created_at": (
            service.created_at.isoformat()
            if service.created_at else None
        ),
        "updated_at": (
            service.updated_at.isoformat()
            if service.updated_at else None
        ),
    }


@services_bp.get("")
def list_services():
    services = Service.query.order_by(Service.id).all()
    return jsonify([
        service_to_dict(service)
        for service in services
    ])


@services_bp.get("/<int:service_id>")
def get_service(service_id: int):
    service = db.session.get(Service, service_id)

    if service is None:
        return jsonify({"error": "Service not found"}), 404

    return jsonify(service_to_dict(service))


@services_bp.post("")
def create_service():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "JSON body is required"}), 400

    name = data.get("name")

    if not name:
        return jsonify({"error": "name is required"}), 400

    if Service.query.filter_by(name=name).first():
        return jsonify({
            "error": "Service with this name already exists"
        }), 409

    service = Service(
        name=name,
        description=data.get("description"),
    )

    db.session.add(service)
    db.session.commit()

    return jsonify(service_to_dict(service)), 201


@services_bp.put("/<int:service_id>")
def update_service(service_id: int):
    service = db.session.get(Service, service_id)

    if service is None:
        return jsonify({"error": "Service not found"}), 404

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "JSON body is required"}), 400

    if "name" in data:
        name = data["name"]

        if not name:
            return jsonify({"error": "name cannot be empty"}), 400

        existing = Service.query.filter(
            Service.name == name,
            Service.id != service_id,
        ).first()

        if existing:
            return jsonify({
                "error": "Service with this name already exists"
            }), 409

        service.name = name

    if "description" in data:
        service.description = data["description"]

    db.session.commit()

    return jsonify(service_to_dict(service))


@services_bp.delete("/<int:service_id>")
def delete_service(service_id: int):
    service = db.session.get(Service, service_id)

    if service is None:
        return jsonify({"error": "Service not found"}), 404

    db.session.delete(service)
    db.session.commit()

    return "", 204
