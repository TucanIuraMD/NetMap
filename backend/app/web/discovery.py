from __future__ import annotations

from flask import Blueprint, render_template

from .api_client import api_get
from .helpers import index_by_id

discovery_bp = Blueprint("discovery", __name__, url_prefix="/discovery")


@discovery_bp.get("")
def discovery_index():
    networks = api_get("/networks")
    sites = index_by_id(api_get("/sites"))

    for network in networks:
        site = sites.get(network.get("site_id"))
        network["site_name"] = site["name"] if site else "—"

    return render_template(
        "discovery/index.html", networks=networks, active_page="discovery"
    )
