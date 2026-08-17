from __future__ import annotations

import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class DiscoveredHost:
    ip_address: str
    hostname: str | None = None
    open_ports: list[int] = field(default_factory=list)


class NetworkScanner:
    """Parallel TCP network scanner."""

    def __init__(
        self,
        timeout: float = 0.5,
        ports: list[int] | None = None,
        workers: int = 50,
    ) -> None:
        self.timeout = timeout
        self.workers = workers
        self.ports = ports or [
            22,
            23,
            53,
            80,
            81,
            443,
            445,
            554,
            8080,
            8443,
        ]

    def scan_host(self, ip_address: str) -> DiscoveredHost | None:
        open_ports: list[int] = []

        for port in self.ports:
            if self._is_port_open(ip_address, port):
                open_ports.append(port)

        hostname = self._resolve_hostname(ip_address)

        if not open_ports and hostname is None:
            return None

        return DiscoveredHost(
            ip_address=ip_address,
            hostname=hostname,
            open_ports=open_ports,
        )

    def scan_network(
        self,
        cidr: str,
        on_progress: Callable[[int, DiscoveredHost | None], None] | None = None,
    ) -> list[DiscoveredHost]:
        """Scan a network, optionally reporting progress.

        ``on_progress`` is called after each host is probed with the
        current scanned count and the newly discovered host (or ``None``
        when the host was not discovered).
        """
        network = ipaddress.ip_network(cidr, strict=False)
        addresses = [str(address) for address in network.hosts()]

        found: list[DiscoveredHost] = []
        scanned = 0

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {
                executor.submit(self.scan_host, address): address
                for address in addresses
            }

            for future in as_completed(futures):
                scanned += 1
                host: DiscoveredHost | None = future.result()

                if host is not None:
                    found.append(host)

                if on_progress is not None:
                    on_progress(scanned, host)

        return found

    def _is_port_open(self, ip_address: str, port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                return sock.connect_ex((ip_address, port)) == 0
        except (OSError, socket.error):
            return False

    @staticmethod
    def _resolve_hostname(ip_address: str) -> str | None:
        try:
            hostname, _, _ = socket.gethostbyaddr(ip_address)
            return hostname
        except (socket.herror, socket.gaierror, OSError):
            return None
