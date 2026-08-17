from __future__ import annotations

from flask import Blueprint, render_template

from .api_client import api_get
from .helpers import device_type_options

topology_bp = Blueprint("topology", __name__, url_prefix="/topology")


@topology_bp.get("")
def topology_view():
    # The graph is fetched client-side from the aggregated
    # GET /api/v1/topology endpoint by static/js/topology.js. The
    # networks and device types below only feed the client-side filters,
    # which are applied as query parameters on that same endpoint.
    networks = api_get("/networks")
    devices = api_get("/devices")
    return render_template(
        "topology/index.html",
        active_page="topology",
        networks=networks,
        device_types=device_type_options(devices),
    )