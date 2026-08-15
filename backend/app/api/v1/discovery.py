from flask import Blueprint, jsonify

from ...extensions import db
from ...models.network import Network
from ...services.discovery_service import DiscoveryService
from ...services.network_scanner import NetworkScanner


discovery_bp = Blueprint(
    "discovery",
    __name__,
    url_prefix="/networks",
)


@discovery_bp.post("/<int:network_id>/discover")
def discover_network(network_id: int):
    network = db.session.get(Network, network_id)

    if network is None:
        return jsonify({"error": "Network not found"}), 404

    if not network.is_active:
        return jsonify({"error": "Network is inactive"}), 400

    scanner = NetworkScanner()
    hosts = scanner.scan_network(network.cidr)

    service = DiscoveryService(network)
    devices = service.sync_hosts(hosts)

    return jsonify(
        {
            "network_id": network.id,
            "cidr": network.cidr,
            "hosts_found": len(hosts),
            "devices_synced": len(devices),
            "devices": [
                {
                    "id": device.id,
                    "name": device.name,
                    "hostname": device.hostname,
                    "device_type": device.device_type,
                }
                for device in devices
            ],
        }
    )