from flask import Blueprint, current_app, jsonify, request

from ...extensions import db
from ...models.network import Network
from ...services.discovery_job_manager import (
    DiscoveryLimitError,
    JobConflictError,
)
from ...services.network_scanner import count_hosts

discovery_jobs_bp = Blueprint(
    "discovery_jobs",
    __name__,
    url_prefix="/discovery",
)


def _manager():
    return current_app.extensions["discovery_job_manager"]


def _parse_network_id(data: dict) -> tuple[int | None, tuple | None]:
    network_id = data.get("network_id")

    if not isinstance(network_id, int):
        return None, (jsonify({"error": "network_id must be an integer"}), 400)

    network = db.session.get(Network, network_id)

    if network is None:
        return None, (jsonify({"error": "Network not found"}), 404)

    if not network.is_active:
        return None, (jsonify({"error": "Network is inactive"}), 400)

    return network.id, None


def _validate_range(network: Network) -> tuple | None:
    try:
        size = count_hosts(network.cidr)
    except ValueError:
        return (jsonify({"error": f"Invalid CIDR: {network.cidr}"}), 400)

    max_hosts = current_app.config["DISCOVERY_MAX_HOSTS"]

    if size > max_hosts:
        return (
            jsonify(
                {
                    "error": (
                        f"Network {network.cidr} is too large: {size} hosts "
                        f"exceed the maximum of {max_hosts} hosts"
                    )
                }
            ),
            400,
        )

    return None


@discovery_jobs_bp.post("/start")
def start_discovery():
    data = request.get_json(silent=True) or {}

    network_id, error = _parse_network_id(data)

    if error is not None:
        return error

    network = db.session.get(Network, network_id)
    error = _validate_range(network)

    if error is not None:
        return error

    try:
        job = _manager().start(network_id)
    except (JobConflictError, DiscoveryLimitError) as exc:
        status_code = 409 if isinstance(exc, JobConflictError) else 400
        return jsonify({"error": str(exc)}), status_code

    return jsonify(job.to_dict()), 202


@discovery_jobs_bp.get("/status")
def discovery_status():
    network_id = request.args.get("network_id", type=int)

    if network_id is None:
        return jsonify({"error": "network_id query parameter is required"}), 400

    job = _manager().status(network_id)

    if job is None:
        return jsonify({"error": "No discovery job found for this network"}), 404

    return jsonify(job.to_dict())


@discovery_jobs_bp.get("/results")
def discovery_results():
    network_id = request.args.get("network_id", type=int)

    if network_id is None:
        return jsonify({"error": "network_id query parameter is required"}), 400

    job = _manager().status(network_id)

    if job is None:
        return jsonify({"error": "No discovery job found for this network"}), 404

    return jsonify(
        {
            "network_id": job.network_id,
            "status": job.status,
            "total_hosts": job.total_hosts,
            "scanned_hosts": job.scanned_hosts,
            "discovered": len(job.discovered_hosts),
            "progress": job.progress,
            "results": job.discovered_hosts,
        }
    )


@discovery_jobs_bp.post("/cancel")
def cancel_discovery():
    data = request.get_json(silent=True) or {}

    network_id = data.get("network_id")

    if not isinstance(network_id, int):
        return jsonify({"error": "network_id must be an integer"}), 400

    job = _manager().cancel(network_id)

    if job is None:
        return jsonify({"error": "No discovery job found for this network"}), 404

    return jsonify(job.to_dict())
