from __future__ import annotations

import socket
import subprocess

from app.extensions import db
from app.models.device import Device
from app.models.interface import Interface
from app.models.ip_address import IPAddress
from app.services.network_scanner import FALLBACK_TCP_PORTS


class MonitoringService:
    """Check device availability and update ``Device.is_active``.

    Availability is determined by an ICMP ping (via the system ``ping``
    binary) with a TCP fallback to the device's known open ports. This
    service only ever toggles the existing ``is_active`` flag; it never
    creates or deletes devices, interfaces, IP addresses, ports or
    services. Device existence is owned by DiscoveryService.
    """

    def __init__(self, timeout: float = 1.0) -> None:
        self.timeout = timeout

    def check_all(self) -> dict:
        """Check every device that has at least one known IP address."""
        devices = (
            Device.query
            .join(Interface)
            .join(IPAddress)
            .distinct()
            .all()
        )

        online = 0
        offline = 0

        for device in devices:
            ip_address = self._primary_ip(device)

            if ip_address is None:
                continue

            reachable = self._is_reachable(device, ip_address)

            if reachable:
                online += 1
            else:
                offline += 1

            if device.is_active != reachable:
                device.is_active = reachable

        db.session.commit()

        return {
            "checked": len(devices),
            "online": online,
            "offline": offline,
        }

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

    def _is_reachable(self, device: Device, ip_address: str) -> bool:
        if self._ping(ip_address):
            return True

        return self._probe_tcp(device, ip_address)

    def _ping(self, ip_address: str) -> bool:
        try:
            result = subprocess.run(
                [
                    "ping",
                    "-n",
                    "-q",
                    "-c",
                    "1",
                    "-W",
                    str(self.timeout),
                    ip_address,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=self.timeout + 2,
            )
        except (OSError, subprocess.SubprocessError):
            return False

        return result.returncode == 0

    def _probe_tcp(self, device: Device, ip_address: str) -> bool:
        ports = [
            port.port_number
            for port in device.ports
            if port.status == "open" and port.protocol == "tcp"
        ]

        if not ports:
            ports = FALLBACK_TCP_PORTS

        for port in ports:
            if self._is_port_open(ip_address, port):
                return True

        return False

    def _is_port_open(self, ip_address: str, port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                return sock.connect_ex((ip_address, port)) == 0
        except (OSError, socket.error):
            return False