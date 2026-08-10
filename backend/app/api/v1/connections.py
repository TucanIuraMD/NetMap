from flask import Blueprint, jsonify, request

from ...extensions import db
from ...models.connection import Connection
from ...models.device import Device
from ...models.port import Port


connections_bp = Blueprint(
    "connections",
    __name__,
    url_prefix="/connections",
)


def connection_to_dict(connection: Connection) -> dict:
    return {
        "id": connection.id,
        "source_device_id": connection.source_device_id,
        "target_device_id": connection.target_device_id,
        "connection_type": connection.connection_type,
        "source_port_id": connection.source_port_id,
        "target_port_id": connection.target_port_id,
        "description": connection.description,
        "is_active": connection.is_active,
        "created_at": (
            connection.created_at.isoformat()
            if connection.created_at else None
        ),
        "updated_at": (
            connection.updated_at.isoformat()
            if connection.updated_at else None
        ),
    }


@connections_bp.get("")
def list_connections():
    connections = Connection.query.order_by(Connection.id).all()
    return jsonify([
        connection_to_dict(connection)
        for connection in connections
    ])


@connections_bp.get("/<int:connection_id>")
def get_connection(connection_id: int):
    connection = db.session.get(Connection, connection_id)

    if connection is None:
        return jsonify({"error": "Connection not found"}), 404

    return jsonify(connection_to_dict(connection))


@connections_bp.post("")
def create_connection():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "JSON body is required"}), 400

    source_device_id = data.get("source_device_id")
    target_device_id = data.get("target_device_id")

    if source_device_id is None:
        return jsonify({"error": "source_device_id is required"}), 400

    if target_device_id is None:
        return jsonify({"error": "target_device_id is required"}), 400

    source_device = db.session.get(Device, source_device_id)

    if source_device is None:
        return jsonify({"error": "Source device not found"}), 404

    target_device = db.session.get(Device, target_device_id)

    if target_device is None:
        return jsonify({"error": "Target device not found"}), 404

    source_port_id = data.get("source_port_id")
    target_port_id = data.get("target_port_id")

    if source_port_id is not None:
        source_port = db.session.get(Port, source_port_id)

        if source_port is None:
            return jsonify({"error": "Source port not found"}), 404

    if target_port_id is not None:
        target_port = db.session.get(Port, target_port_id)

        if target_port is None:
            return jsonify({"error": "Target port not found"}), 404

    connection = Connection(
        source_device_id=source_device_id,
        target_device_id=target_device_id,
        connection_type=data.get("connection_type", "network"),
        source_port_id=source_port_id,
        target_port_id=target_port_id,
        description=data.get("description"),
        is_active=data.get("is_active", True),
    )

    db.session.add(connection)
    db.session.commit()

    return jsonify(connection_to_dict(connection)), 201


@connections_bp.put("/<int:connection_id>")
def update_connection(connection_id: int):
    connection = db.session.get(Connection, connection_id)

    if connection is None:
        return jsonify({"error": "Connection not found"}), 404

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "JSON body is required"}), 400

    if "source_device_id" in data:
        source_device_id = data["source_device_id"]

        if db.session.get(Device, source_device_id) is None:
            return jsonify({"error": "Source device not found"}), 404

        connection.source_device_id = source_device_id

    if "target_device_id" in data:
        target_device_id = data["target_device_id"]

        if db.session.get(Device, target_device_id) is None:
            return jsonify({"error": "Target device not found"}), 404

        connection.target_device_id = target_device_id

    if "connection_type" in data:
        connection.connection_type = data["connection_type"]

    if "source_port_id" in data:
        source_port_id = data["source_port_id"]

        if source_port_id is not None:
            if db.session.get(Port, source_port_id) is None:
                return jsonify({"error": "Source port not found"}), 404

        connection.source_port_id = source_port_id

    if "target_port_id" in data:
        target_port_id = data["target_port_id"]

        if target_port_id is not None:
            if db.session.get(Port, target_port_id) is None:
                return jsonify({"error": "Target port not found"}), 404

        connection.target_port_id = target_port_id

    if "description" in data:
        connection.description = data["description"]

    if "is_active" in data:
        connection.is_active = data["is_active"]

    db.session.commit()

    return jsonify(connection_to_dict(connection))


@connections_bp.delete("/<int:connection_id>")
def delete_connection(connection_id: int):
    connection = db.session.get(Connection, connection_id)

    if connection is None:
        return jsonify({"error": "Connection not found"}), 404

    db.session.delete(connection)
    db.session.commit()

    return "", 204
