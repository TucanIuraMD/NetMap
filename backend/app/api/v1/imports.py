from flask import Blueprint, jsonify, request

from ...services.port_import import (
    ImportItem,
    PortImportService,
)
from .validation import (
    validate_port_number,
    validate_port_protocol,
)


imports_bp = Blueprint(
    "imports",
    __name__,
    url_prefix="/imports",
)


@imports_bp.post("/ports")
def import_ports():
    data = request.get_json(silent=True)

    if not data or "items" not in data:
        return jsonify({"error": "JSON body with an 'items' list is required"}), 400

    items_data = data["items"]

    if not isinstance(items_data, list) or not items_data:
        return jsonify({"error": "'items' must be a non-empty list"}), 400

    items = []

    for index, row in enumerate(items_data):
        if not isinstance(row, dict):
            return jsonify({
                "error": f"items[{index}] must be an object"
            }), 400

        device = row.get("device")
        port_number = row.get("port")
        protocol = row.get("protocol")

        if device is None:
            return jsonify({
                "error": f"items[{index}].device is required"
            }), 400

        port_number, error = validate_port_number(port_number)
        if error:
            return jsonify({"error": f"items[{index}]: {error}"}), 400

        protocol, error = validate_port_protocol(protocol)
        if error:
            return jsonify({"error": f"items[{index}]: {error}"}), 400

        items.append(
            ImportItem(
                device=device,
                port_number=port_number,
                protocol=protocol,
                display_name=row.get("display_name"),
                description=row.get("description"),
            )
        )

    result = PortImportService().sync(items)

    return jsonify(result.to_dict())
