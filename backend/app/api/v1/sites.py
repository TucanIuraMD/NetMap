from flask import Blueprint, jsonify, request

from ...extensions import db
from ...models.site import Site

sites_bp = Blueprint("sites", __name__, url_prefix="/sites")


def site_to_dict(site: Site) -> dict:
    return {
        "id": site.id,
        "name": site.name,
        "description": site.description,
        "location": site.location,
        "contact": site.contact,
        "is_active": site.is_active,
        "created_at": site.created_at.isoformat() if site.created_at else None,
        "updated_at": site.updated_at.isoformat() if site.updated_at else None,
    }


@sites_bp.get("")
def list_sites():
    sites = Site.query.order_by(Site.id).all()
    return jsonify([site_to_dict(site) for site in sites])


@sites_bp.get("/<int:site_id>")
def get_site(site_id: int):
    site = db.session.get(Site, site_id)

    if site is None:
        return jsonify({"error": "Site not found"}), 404

    return jsonify(site_to_dict(site))


@sites_bp.post("")
def create_site():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "JSON body is required"}), 400

    name = data.get("name")

    if not name:
        return jsonify({"error": "name is required"}), 400

    if Site.query.filter_by(name=name).first():
        return jsonify({"error": "Site with this name already exists"}), 409

    site = Site(
        name=name,
        description=data.get("description"),
        location=data.get("location"),
        contact=data.get("contact"),
        is_active=data.get("is_active", True),
    )

    db.session.add(site)
    db.session.commit()

    return jsonify(site_to_dict(site)), 201


@sites_bp.put("/<int:site_id>")
def update_site(site_id: int):
    site = db.session.get(Site, site_id)

    if site is None:
        return jsonify({"error": "Site not found"}), 404

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "JSON body is required"}), 400

    if "name" in data:
        name = data["name"]

        if not name:
            return jsonify({"error": "name cannot be empty"}), 400

        existing = Site.query.filter(
            Site.name == name,
            Site.id != site_id,
        ).first()

        if existing:
            return jsonify({"error": "Site with this name already exists"}), 409

        site.name = name

    if "description" in data:
        site.description = data["description"]

    if "location" in data:
        site.location = data["location"]

    if "contact" in data:
        site.contact = data["contact"]

    if "is_active" in data:
        site.is_active = data["is_active"]

    db.session.commit()

    return jsonify(site_to_dict(site))


@sites_bp.delete("/<int:site_id>")
def delete_site(site_id: int):
    site = db.session.get(Site, site_id)

    if site is None:
        return jsonify({"error": "Site not found"}), 404

    db.session.delete(site)
    db.session.commit()

    return "", 204
