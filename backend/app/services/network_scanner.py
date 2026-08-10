from __future__ import annotations

import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field


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

    def scan_network(self, cidr: str) -> list[DiscoveredHost]:
        network = ipaddress.ip_network(cidr, strict=False)
        addresses = [str(address) for address in network.hosts()]

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            results = executor.map(self.scan_host, addresses)

        return [
            result
            for result in results
            if result is not None
        ]

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
