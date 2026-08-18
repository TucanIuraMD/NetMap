"""Single-device TCP port scanning.

Probes a fixed list of well-known TCP ports against a single device's
primary IP using bounded parallel socket connects. Requires no
privileges (plain TCP only). Open ports are upserted into the inventory
through the existing ``Port``/``Service`` models, mirroring
``PortImportService`` semantics: manual data is never overwritten.

Only one scan may run per device at a time. The guard lives in-process
memory only: it protects against concurrent requests inside a single
Gunicorn worker (consistent with ``DiscoveryJobManager``) and does not
span multiple worker processes.
"""

from __future__ import annotations

import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Callable

from app.extensions import db
from app.models.device import Device
from app.models.interface import Interface
from app.models.ip_address import IPAddress
from app.models.port import Port
from app.models.service import Service
from app.services.port_import import WEB_PORT_SCHEMES
from app.web.helpers import port_service_name


class PortScanError(Exception):
    """Base class for port scanning errors."""


class PortScanConflictError(PortScanError):
    """Raised when a scan is already running for the same device."""


class NoIpAddressError(PortScanError):
    """Raised when the device has no usable IP address to scan."""


@dataclass
class PortScanResult:
    """Outcome of one single-device port scan."""

    device_id: int
    ip_address: str
    ports_scanned: int
    open_ports: list[int] = field(default_factory=list)
    elapsed_ms: int = 0
    created: list[dict] = field(default_factory=list)
    updated: list[dict] = field(default_factory=list)


class PortScannerService:
    """Scan a single device's TCP ports and sync results to the inventory."""

    SCAN_PORTS = [
        20, 21, 22, 23, 25, 53, 67, 68, 69, 80,
        81, 110, 123, 143, 161, 162, 389, 443, 445, 465,
        514, 554, 587, 636, 993, 995, 1433, 1521, 1723, 2375,
        2376, 3000, 3306, 3389, 5432, 6379, 8000, 8006, 8080, 8443,
    ]

    def __init__(
        self,
        timeout: float = 1.0,
        concurrency: int = 25,
        probe: Callable[[str, int], bool] | None = None,
    ) -> None:
        self.timeout = timeout
        self.concurrency = concurrency
        self._probe = probe or self._tcp_probe
        self._active: set[int] = set()
        self._lock = threading.Lock()

    def scan_device(
        self,
        device: Device,
        ports: list[int] | None = None,
    ) -> PortScanResult:
        if not self._acquire(device.id):
            raise PortScanConflictError(
                f"A port scan is already running for device {device.id}"
            )

        try:
            return self._scan_device(device, ports)
        finally:
            self._release(device.id)

    # --- internals ---------------------------------------------------

    def _scan_device(
        self,
        device: Device,
        ports: list[int] | None,
    ) -> PortScanResult:
        ip_address = self._primary_ip(device)

        if ip_address is None:
            raise NoIpAddressError(
                f"Device {device.id} has no IP address to scan"
            )

        ports = list(ports) if ports is not None else list(self.SCAN_PORTS)
        open_ports: list[int] = []

        started = time.monotonic()

        with ThreadPoolExecutor(max_workers=max(1, self.concurrency)) as executor:
            futures = {
                executor.submit(self._probe, ip_address, port): port
                for port in ports
            }

            for future in as_completed(futures):
                port = futures[future]

                try:
                    if future.result():
                        open_ports.append(port)
                except Exception:
                    continue

        elapsed_ms = int((time.monotonic() - started) * 1000)
        open_ports.sort()

        created, updated = self._sync_ports(device, open_ports)

        return PortScanResult(
            device_id=device.id,
            ip_address=ip_address,
            ports_scanned=len(ports),
            open_ports=open_ports,
            elapsed_ms=elapsed_ms,
            created=created,
            updated=updated,
        )

    def _tcp_probe(self, ip_address: str, port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                return sock.connect_ex((ip_address, port)) == 0
        except (OSError, socket.error):
            return False

    def _primary_ip(self, device: Device) -> str | None:
        primary = (
            IPAddress.query
            .join(Interface)
            .filter(
                Interface.device_id == device.id,
                IPAddress.is_primary.is_(True),
            )
            .first()
        )

        if primary is not None:
            return primary.address

        any_ip = (
            IPAddress.query
            .join(Interface)
            .filter(Interface.device_id == device.id)
            .first()
        )

        if any_ip is not None:
            return any_ip.address

        return None

    def _sync_ports(
        self,
        device: Device,
        open_ports: list[int],
    ) -> tuple[list[dict], list[dict]]:
        """Upsert open ports, never overwriting manual data.

        Mirrors ``PortImportService._sync_item``: existing ports are only
        re-activated and backfilled with a display name when none was set
        by hand; missing ports are created with the standard name and web
        scheme. Ports outside ``open_ports`` are left untouched.
        """
        created: list[dict] = []
        updated: list[dict] = []

        for port_number in open_ports:
            existing = Port.query.filter_by(
                device_id=device.id,
                port_number=port_number,
                protocol="tcp",
            ).first()

            if existing is not None:
                changed = False

                if existing.status != "open":
                    existing.status = "open"
                    changed = True

                display_name = self._display_name(port_number)

                if (
                    not (existing.display_name or "").strip()
                    and display_name
                ):
                    existing.display_name = display_name
                    changed = True

                if changed:
                    updated.append(self._port_record(existing, port_number))
                continue

            service_id = None
            display_name = self._display_name(port_number)

            if display_name:
                service = Service.query.filter_by(name=display_name).first()

                if service is None:
                    service = Service(name=display_name)
                    db.session.add(service)
                    db.session.flush()

                service_id = service.id

            port = Port(
                device_id=device.id,
                service_id=service_id,
                port_number=port_number,
                protocol="tcp",
                status="open",
                display_name=display_name,
                web_scheme=WEB_PORT_SCHEMES.get((port_number, "tcp")),
                description="scan:auto",
            )
            db.session.add(port)
            db.session.flush()
            created.append(self._port_record(port, port_number))

        db.session.commit()
        return created, updated

    @staticmethod
    def _display_name(port_number: int) -> str | None:
        return port_service_name(
            {
                "port_number": port_number,
                "protocol": "tcp",
                "display_name": None,
            }
        )

    @staticmethod
    def _port_record(port: Port, port_number: int) -> dict:
        return {
            "id": port.id,
            "port": port_number,
            "protocol": "tcp",
            "status": "open",
            "display_name": port.display_name,
            "web_scheme": port.web_scheme,
        }

    def _acquire(self, device_id: int) -> bool:
        with self._lock:
            if device_id in self._active:
                return False

            self._active.add(device_id)
            return True

    def _release(self, device_id: int) -> None:
        with self._lock:
            self._active.discard(device_id)
