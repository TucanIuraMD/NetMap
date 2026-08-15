from __future__ import annotations

from flask import Blueprint, render_template

topology_bp = Blueprint("topology", __name__, url_prefix="/topology")


@topology_bp.get("")
def topology_view():
    # The graph itself is fetched client-side from the public
    # /api/v1/devices and /api/v1/connections endpoints by
    # static/js/topology.js — no server-side aggregation endpoint
    # exists (see docs/UI_STATUS.md, backend gaps).
    return render_template("topology/index.html", active_page="topology")
