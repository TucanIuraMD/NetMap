"""Unit tests for PortScannerService."""

from __future__ import annotations

import threading
import time

import pytest

from app.extensions import db
from app.models.device import Device
from app.models.port import Port
from app.services.port_scanner import (
    NoIpAddressError,
    PortScanConflictError,
    PortScannerService,
)
from tests.conftest import create_device


def make_probe(open_ports: set[int]):
    """Return a probe that reports exactly ``open_ports`` as reachable."""
    return lambda ip, port: port in open_ports


def test_scan_ports_list_has_exactly_40_unique_ports():
    ports = PortScannerService.SCAN_PORTS
    assert len(ports) == 40
    assert len(set(ports)) == 40


def test_scan_creates_open_ports(app):
    device_id = create_device(app)
    service = PortScannerService(probe=make_probe({22, 80}))

    with app.app_context():
        device = db.session.get(Device, device_id)
        result = service.scan_device(device)

        assert result.ip_address == "192.168.50.10"
        assert result.ports_scanned == 40
        assert result.open_ports == [22, 80]
        assert result.elapsed_ms >= 0

        ports = (
            Port.query.filter_by(device_id=device_id)
            .order_by(Port.port_number)
            .all()
        )
        assert [p.port_number for p in ports] == [22, 80]
        assert all(p.status == "open" for p in ports)
        assert all(p.protocol == "tcp" for p in ports)

        by_number = {p.port_number: p for p in ports}
        assert by_number[22].display_name == "SSH / SFTP"
        assert by_number[80].display_name == "HTTP"
        assert by_number[80].web_scheme == "http"
        assert by_number[80].description == "scan:auto"


def test_repeat_scan_creates_no_duplicates(app):
    device_id = create_device(app)
    service = PortScannerService(probe=make_probe({22, 80, 443}))

    with app.app_context():
        device = db.session.get(Device, device_id)
        first = service.scan_device(device)
        second = service.scan_device(device)

        assert first.open_ports == [22, 80, 443]
        assert len(first.created) == 3
        assert first.updated == []

        assert second.open_ports == [22, 80, 443]
        assert second.created == []
        assert second.updated == []

        assert Port.query.filter_by(device_id=device_id).count() == 3


def test_scan_reactivates_closed_port(app):
    device_id = create_device(app)
    service = PortScannerService(probe=make_probe({22}))

    with app.app_context():
        device = db.session.get(Device, device_id)
        service.scan_device(device)

        port = Port.query.filter_by(device_id=device_id, port_number=22).first()
        port.status = "closed"
        db.session.commit()

        result = service.scan_device(device)

        port = Port.query.filter_by(device_id=device_id, port_number=22).first()
        assert port.status == "open"
        assert [item["port"] for item in result.updated] == [22]
        assert result.created == []


def test_scan_does_not_overwrite_manual_display_name(app):
    device_id = create_device(app)
    service = PortScannerService(probe=make_probe({22}))

    with app.app_context():
        device = db.session.get(Device, device_id)
        service.scan_device(device)

        port = Port.query.filter_by(device_id=device_id, port_number=22).first()
        port.display_name = "Custom SSH"
        db.session.commit()

        service.scan_device(device)

        port = Port.query.filter_by(device_id=device_id, port_number=22).first()
        assert port.display_name == "Custom SSH"


def test_scan_requires_ip_address(app):
    with app.app_context():
        from app.models.network import Network
        from app.models.site import Site

        site = Site(name="No Ip Site")
        db.session.add(site)
        db.session.flush()
        network = Network(
            site_id=site.id,
            name="No Ip Network",
            cidr="192.168.60.0/24",
        )
        db.session.add(network)
        db.session.flush()
        device = Device(network_id=network.id, name="no-ip")
        db.session.add(device)
        db.session.commit()

        service = PortScannerService(probe=make_probe({22}))

        with pytest.raises(NoIpAddressError):
            service.scan_device(device)


def test_second_concurrent_scan_conflicts(app):
    device_id = create_device(app)
    started = threading.Event()
    release = threading.Event()
    results: list = []

    def blocking_probe(ip, port):
        started.set()
        release.wait(timeout=5)
        return True

    service = PortScannerService(probe=blocking_probe, concurrency=2)

    with app.app_context():
        device = db.session.get(Device, device_id)

        def run_scan():
            with app.app_context():
                results.append(service.scan_device(device))

        worker = threading.Thread(target=run_scan)
        worker.start()

        assert started.wait(timeout=2)

        with pytest.raises(PortScanConflictError):
            service.scan_device(device)

        release.set()
        worker.join(timeout=5)
        assert not worker.is_alive()
        assert len(results) == 1

        # After the first scan finished the device is free again.
        service2 = PortScannerService(probe=make_probe({22}))
        result = service2.scan_device(device)
        assert result.open_ports == [22]


def test_concurrency_is_bounded(app):
    device_id = create_device(app)
    active = 0
    max_active = 0
    lock = threading.Lock()

    def counting_probe(ip, port):
        nonlocal active, max_active
        with lock:
            active += 1
            max_active = max(max_active, active)
        time.sleep(0.02)
        with lock:
            active -= 1
        return True

    service = PortScannerService(probe=counting_probe, concurrency=5)

    with app.app_context():
        device = db.session.get(Device, device_id)
        result = service.scan_device(device)

        assert result.ports_scanned == 40
        assert len(result.open_ports) == 40
        assert max_active <= 5
        assert max_active == 5
