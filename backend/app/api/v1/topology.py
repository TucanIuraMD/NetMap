from flask import Blueprint, jsonify, request

from ...services.topology_service import TopologyService


topology_bp = Blueprint("topology", __name__, url_prefix="/topology")


@topology_bp.get("")
def get_topology():
    args = request.args

    network_id = args.get("network_id", "").strip()
    device_type = args.get("device_type", "").strip()
    status = args.get("status", "").strip()

    topology = TopologyService.build(
        network_id=(
            int(network_id)
            if network_id.isdigit() else None
        ),
        device_type=device_type or None,
        status=status or None,
    )

    return jsonify(topology)