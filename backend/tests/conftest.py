"""Shared fixtures for the NetMap test suite."""

from __future__ import annotations

import pytest
from flask import Flask

from app.api.v1 import api_v1
from app.extensions import db
from app.models.connection import Connection
from app.models.device import Device
from app.models.interface import Interface
from app.models.ip_address import IPAddress
from app.models.network import Network
from app.models.port import Port
from app.models.service import Service
from app.models.site import Site
from app.services.port_scanner import PortScannerService


@pytest.fixture
def app():
    flask_app = Flask(__name__)
    flask_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite://",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db.init_app(flask_app)
    flask_app.register_blueprint(api_v1, url_prefix="/api/v1")

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def create_device(
    app,
    ip: str = "192.168.50.10",
    name: str = "test-host",
) -> int:
    """Create a Site/Network/Device/Interface/IPAddress chain and return device id."""
    with app.app_context():
        site = Site(name="Test Site")
        db.session.add(site)
        db.session.flush()

        network = Network(
            site_id=site.id,
            name="Test Network",
            cidr="192.168.50.0/24",
            is_active=True,
        )
        db.session.add(network)
        db.session.flush()

        device = Device(
            network_id=network.id,
            name=name,
            is_active=True,
        )
        db.session.add(device)
        db.session.flush()

        interface = Interface(
            device_id=device.id,
            name="eth0",
            is_active=True,
        )
        db.session.add(interface)
        db.session.flush()

        ip_address = IPAddress(
            interface_id=interface.id,
            address=ip,
            version=4,
            is_primary=True,
        )
        db.session.add(ip_address)
        db.session.commit()

        return device.id
