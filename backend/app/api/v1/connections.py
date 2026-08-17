from flask import Blueprint, jsonify, request
from sqlalchemy import or_

from ...extensions import db
from ...models.connection import Connection
from ...models.device import Device
from ...models.interface import Interface
from ...models.port import Port
from .validation import validate_connection_type


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
        "source_interface_id": connection.source_interface_id,
        "target_interface_id": connection.target_interface_id,
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


def _interface_for_device(interface_id, device_id, label):
    if interface_id is None:
        return None, None, None

    interface = db.session.get(Interface, interface_id)

    if interface is None:
        return interface, f"{label} interface not found", 404

    if interface.device_id != device_id:
        return (
            interface,
            f"{label} interface does not belong to source/target device",
            400,
        )

    return interface, None, None


def _validate_interface_pair(source, target, label="Connection"):
    if (
        source is not None
        and target is not None
        and source.id == target.id
    ):
        return f"{label} source and target interfaces must differ", 400

    return None, None


def _nullable_match(column, value):
    if value is None:
        return column.is_(None)

    return column == value


def _find_duplicate_connection(
    source_device_id,
    target_device_id,
    source_port_id,
    target_port_id,
    source_interface_id,
    target_interface_id,
    exclude_id: int | None = None,
) -> Connection | None:
    """Find an existing connection with the same endpoint pair.

    A duplicate is defined by the device pair plus the optional port
    and interface endpoints. ``connection_type`` is deliberately not
    part of the identity, so the same physical link cannot be recorded
    twice with different types.
    """
    query = Connection.query.filter(
        Connection.source_device_id == source_device_id,
        Connection.target_device_id == target_device_id,
        _nullable_match(Connection.source_port_id, source_port_id),
        _nullable_match(Connection.target_port_id, target_port_id),
        _nullable_match(Connection.source_interface_id, source_interface_id),
        _nullable_match(Connection.target_interface_id, target_interface_id),
    )

    if exclude_id is not None:
        query = query.filter(Connection.id != exclude_id)

    return query.first()


def _validate_port_ownership(
    port_id,
    device_id,
    label: str,
    is_source: bool = True,
):
    """Validate an optional port reference belongs to the device.

    Returns ``(port, error, status_code)``. ``None`` ports are valid
    (device-level connections), as long as they were passed as ``None``
    explicitly — an empty-string port is rejected here.
    """
    if port_id is None:
        return None, None, None

    port = db.session.get(Port, port_id)

    if port is None:
        return port, f"{label} port not found", 404

    if port.device_id != device_id:
        return (
            port,
            f"{label} port does not belong to the {is_source and 'source' or 'target'} device",
            400,
        )

    return port, None, None


def _paginate(query, page: int, per_page: int) -> dict:
    page = max(page, 1)
    per_page = max(min(per_page, 500), 1)

    total = query.count()
    total_pages = max((total + per_page - 1) // per_page, 1)
    items = (
        query.offset((page - 1) * per_page).limit(per_page).all()
    )

    return {
        "items": [connection_to_dict(connection) for connection in items],
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
    }


@connections_bp.get("")
def list_connections():
    args = request.args

    # Backward-compatible fast path: no query parameters at all means
    # "return everything", exactly as before (a bare JSON array).
    if not args:
        connections = Connection.query.order_by(Connection.id).all()
        return jsonify([
            connection_to_dict(connection)
            for connection in connections
        ])

    query = Connection.query

    device_id = args.get("device_id", "").strip()
    if device_id:
        try:
            device_id = int(device_id)
        except ValueError:
            device_id = None

        if device_id is not None:
            query = query.filter(
                or_(
                    Connection.source_device_id == device_id,
                    Connection.target_device_id == device_id,
                )
            )

    is_active = args.get("is_active", "").strip()
    if is_active in {"true", "1", "yes"}:
        query = query.filter(Connection.is_active.is_(True))
    elif is_active in {"false", "0", "no"}:
        query = query.filter(Connection.is_active.is_(False))

    connection_type = args.get("connection_type", "").strip()
    if connection_type:
        query = query.filter(Connection.connection_type == connection_type)

    page = args.get("page", 1, type=int)
    per_page = args.get("per_page", type=int)
    if per_page is None:
        per_page = args.get("page_size", 50, type=int)

    return jsonify(_paginate(query, page, per_page))


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

    if source_device_id == target_device_id:
        return jsonify({"error": "Source and target devices must differ"}), 400

    source_port_id = data.get("source_port_id")
    target_port_id = data.get("target_port_id")
    source_interface_id = data.get("source_interface_id")
    target_interface_id = data.get("target_interface_id")

    source_port, error, code = _validate_port_ownership(
        source_port_id, source_device_id, "Source"
    )
    if error:
        return jsonify({"error": error}), code

    target_port, error, code = _validate_port_ownership(
        target_port_id, target_device_id, "Target", is_source=False
    )
    if error:
        return jsonify({"error": error}), code

    source_interface, error, code = _interface_for_device(
        source_interface_id, source_device_id, "Source"
    )
    if error:
        return jsonify({"error": error}), code

    target_interface, error, code = _interface_for_device(
        target_interface_id, target_device_id, "Target"
    )
    if error:
        return jsonify({"error": error}), code

    error, code = _validate_interface_pair(
        source_interface, target_interface
    )
    if error:
        return jsonify({"error": error}), code

    connection_type, error = validate_connection_type(
        data.get("connection_type", "network")
    )
    if error:
        return jsonify({"error": error}), 400

    if _find_duplicate_connection(
        source_device_id,
        target_device_id,
        source_port_id,
        target_port_id,
        source_interface_id,
        target_interface_id,
    ):
        return jsonify({"error": "Connection already exists"}), 409

    connection = Connection(
        source_device_id=source_device_id,
        target_device_id=target_device_id,
        connection_type=connection_type,
        source_port_id=source_port_id,
        target_port_id=target_port_id,
        source_interface_id=source_interface_id,
        target_interface_id=target_interface_id,
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

    if connection.source_device_id == connection.target_device_id:
        return jsonify({"error": "Source and target devices must differ"}), 400

    if "connection_type" in data:
        connection_type, error = validate_connection_type(
            data["connection_type"]
        )
        if error:
            return jsonify({"error": error}), 400

        connection.connection_type = connection_type

    if "source_port_id" in data:
        source_port_id = data["source_port_id"]

        source_port, error, code = _validate_port_ownership(
            source_port_id,
            connection.source_device_id,
            "Source",
        )
        if error:
            return jsonify({"error": error}), code

        connection.source_port_id = source_port_id

    if "target_port_id" in data:
        target_port_id = data["target_port_id"]

        target_port, error, code = _validate_port_ownership(
            target_port_id,
            connection.target_device_id,
            "Target",
            is_source=False,
        )
        if error:
            return jsonify({"error": error}), code

        connection.target_port_id = target_port_id

    if "source_interface_id" in data:
        source_interface_id = data["source_interface_id"]

        source_interface, error, code = _interface_for_device(
            source_interface_id,
            connection.source_device_id,
            "Source",
        )
        if error:
            return jsonify({"error": error}), code

        connection.source_interface_id = source_interface_id

    if "target_interface_id" in data:
        target_interface_id = data["target_interface_id"]

        target_interface, error, code = _interface_for_device(
            target_interface_id,
            connection.target_device_id,
            "Target",
        )
        if error:
            return jsonify({"error": error}), code

        connection.target_interface_id = target_interface_id

    error, code = _validate_interface_pair(
        db.session.get(Interface, connection.source_interface_id)
        if connection.source_interface_id else None,
        db.session.get(Interface, connection.target_interface_id)
        if connection.target_interface_id else None,
    )
    if error:
        return jsonify({"error": error}), code

    if "description" in data:
        connection.description = data["description"]

    if "is_active" in data:
        connection.is_active = data["is_active"]

    if _find_duplicate_connection(
        connection.source_device_id,
        connection.target_device_id,
        connection.source_port_id,
        connection.target_port_id,
        connection.source_interface_id,
        connection.target_interface_id,
        exclude_id=connection.id,
    ):
        return jsonify({"error": "Connection already exists"}), 409

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
