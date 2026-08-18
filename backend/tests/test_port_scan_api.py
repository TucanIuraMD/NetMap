"""API tests for POST /api/v1/devices/<id>/ports/scan."""

from __future__ import annotations

import threading
import time

from app.extensions import db
from app.models.device import Device
from app.models.network import Network
from app.models.site import Site
from app.services.port_scanner import PortScannerService
from tests.conftest import create_device


def _bind_service(app, probe):
    app.extensions["port_scanner_service"] = PortScannerService(probe=probe)


def _create_device_without_ip(app):
    with app.app_context():
        site = Site(name="No Ip Site")
        db.session.add(site)
        db.session.flush()
        network = Network(
            site_id=site.id,
            name="No Ip Network",
            cidr="10.0.0.0/24",
        )
        db.session.add(network)
        db.session.flush()
        device = Device(network_id=network.id, name="no-ip")
        db.session.add(device)
        db.session.commit()
        return device.id


def test_scan_endpoint_404(app, client):
    _bind_service(app, lambda ip, port: False)
    resp = client.post("/api/v1/devices/999/ports/scan")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "Device not found"


def test_scan_endpoint_requires_ip(app, client):
    device_id = _create_device_without_ip(app)
    _bind_service(app, lambda ip, port: False)
    resp = client.post(f"/api/v1/devices/{device_id}/ports/scan")
    assert resp.status_code == 400
    assert "no IP address" in resp.get_json()["error"]


def test_scan_endpoint_creates_ports(app, client):
    device_id = create_device(app)
    _bind_service(app, lambda ip, port: port in {22, 443})

    resp = client.post(f"/api/v1/devices/{device_id}/ports/scan")

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ip_address"] == "192.168.50.10"
    assert data["ports_scanned"] == 40
    assert data["open_ports"] == [22, 443]
    assert data["elapsed_ms"] >= 0
    assert len(data["created"]) == 2
    assert data["updated"] == []


def test_scan_endpoint_409_while_running(app, client):
    device_id = create_device(app)
    started = threading.Event()
    release = threading.Event()

    def blocking_probe(ip, port):
        started.set()
        release.wait(timeout=5)
        return True

    _bind_service(app, blocking_probe)

    first_client = app.test_client()
    outcome: dict = {}

    def run_first():
        outcome["resp"] = first_client.post(
            f"/api/v1/devices/{device_id}/ports/scan"
        )

    thread = threading.Thread(target=run_first)
    thread.start()

    assert started.wait(timeout=2)

    resp = client.post(f"/api/v1/devices/{device_id}/ports/scan")
    assert resp.status_code == 409
    assert "already running" in resp.get_json()["error"]

    release.set()
    thread.join(timeout=5)
    assert not thread.is_alive()
    assert outcome["resp"].status_code == 200
