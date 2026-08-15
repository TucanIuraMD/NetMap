from __future__ import annotations

from flask import Blueprint, render_template, request

from .api_client import ApiError, api_delete, api_get, api_post, api_put
from .helpers import index_by_id

networks_bp = Blueprint("networks", __name__, url_prefix="/networks")


def _networks_with_counts() -> list[dict]:
    networks = api_get("/networks")
    sites = index_by_id(api_get("/sites"))
    devices = api_get("/devices")

    for network in networks:
        site = sites.get(network.get("site_id"))
        network["site_name"] = site["name"] if site else "—"
        network_devices = [
            d for d in devices if d.get("network_id") == network["id"]
        ]
        network["device_count"] = len(network_devices)
        network["active_device_count"] = sum(
            1 for d in network_devices if d.get("is_active")
        )

    return networks


@networks_bp.get("")
def list_networks():
    return render_template(
        "networks/list.html",
        networks=_networks_with_counts(),
        active_page="networks",
    )


@networks_bp.get("/new")
def new_network_form():
    sites = api_get("/sites")
    return render_template(
        "networks/_form.html", network=None, sites=sites, error=None
    )


@networks_bp.get("/<int:network_id>/edit")
def edit_network_form(network_id: int):
    try:
        network = api_get(f"/networks/{network_id}")
    except ApiError as exc:
        return (
            f'<div class="modal-header"><h5 class="modal-title">Not found</h5>'
            f'<button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>'
            f'<div class="modal-body"><div class="alert alert-danger mb-0">'
            f"{exc.message}</div></div>",
            exc.status_code,
        )

    sites = api_get("/sites")
    return render_template(
        "networks/_form.html", network=network, sites=sites, error=None
    )


def _network_form_payload() -> dict:
    return {
        "name": request.form.get("name", "").strip(),
        "cidr": request.form.get("cidr", "").strip(),
        "site_id": request.form.get("site_id", type=int),
        "description": request.form.get("description", "").strip() or None,
        "is_active": request.form.get("is_active") == "on",
    }


@networks_bp.post("")
def create_network():
    payload = _network_form_payload()

    try:
        api_post("/networks", payload)
    except ApiError as exc:
        sites = api_get("/sites")
        return render_template(
            "networks/_form.html",
            network=payload,
            sites=sites,
            error=exc.message,
        ), exc.status_code

    response = render_template(
        "networks/_table.html", networks=_networks_with_counts()
    )
    return response, 200, {"HX-Trigger": "network-saved"}


@networks_bp.put("/<int:network_id>")
def update_network(network_id: int):
    payload = _network_form_payload()

    try:
        api_put(f"/networks/{network_id}", payload)
    except ApiError as exc:
        sites = api_get("/sites")
        payload["id"] = network_id
        return render_template(
            "networks/_form.html",
            network=payload,
            sites=sites,
            error=exc.message,
        ), exc.status_code

    # Bugfix: same pattern as devices.update_device — target is now
    # #nm-modal-content (always present), refreshed table is returned
    # as an out-of-band swap for #networks-table-wrapper, which only
    # exists on the Networks List page and is skipped elsewhere.
    table_html = render_template(
        "networks/_table.html", networks=_networks_with_counts()
    )
    response = (
        f'<div id="networks-table-wrapper" hx-swap-oob="true">'
        f"{table_html}</div>"
    )
    return response, 200, {"HX-Trigger": "network-saved"}


@networks_bp.delete("/<int:network_id>")
def delete_network(network_id: int):
    try:
        api_delete(f"/networks/{network_id}")
    except ApiError as exc:
        return (
            f'<div class="alert alert-danger py-2 mb-2">{exc.message}</div>',
            exc.status_code,
        )

    return render_template("networks/_table.html", networks=_networks_with_counts())


@networks_bp.get("/<int:network_id>")
def network_details(network_id: int):
    try:
        network = api_get(f"/networks/{network_id}")
    except ApiError as exc:
        return render_template("errors/404.html", message=exc.message), exc.status_code

    site = api_get(f"/sites/{network['site_id']}")
    devices = [
        d for d in api_get("/devices")
        if d.get("network_id") == network_id
    ]

    return render_template(
        "networks/details.html",
        network=network,
        site=site,
        devices=devices,
        device_count=len(devices),
        active_device_count=sum(1 for d in devices if d.get("is_active")),
        active_page="networks",
    )


@networks_bp.post("/<int:network_id>/discover")
def discover_network(network_id: int):
    """Trigger discovery.

    NOTE: the backend endpoint (POST /api/v1/networks/<id>/discover)
    is synchronous — it runs the scan and returns the final result
    in the same HTTP response. There is no discovery/status polling
    endpoint (docs/03_API.md describes one under /discovery/*, but it
    is not implemented). The UI therefore shows a blocking HTMX
    request with a spinner (hx-indicator) rather than polling.
    """
    try:
        result = api_post(f"/networks/{network_id}/discover", {})
    except ApiError as exc:
        return render_template(
            "networks/_discovery_result.html",
            error=exc.message,
            result=None,
            network_id=network_id,
        ), exc.status_code

    devices = [
        d for d in api_get("/devices")
        if d.get("network_id") == network_id
    ]

    return render_template(
        "networks/_discovery_result.html",
        error=None,
        result=result,
        network_id=network_id,
        devices=devices,
    )
