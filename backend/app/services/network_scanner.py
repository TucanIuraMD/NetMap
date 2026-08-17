from __future__ import annotations

import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable

from app.services.icmp_probe import ICMPProbe, ICMPUnavailableError


class DiscoveryRangeError(Exception):
    """Base class for discovery range validation errors."""


class InvalidCIDRError(DiscoveryRangeError):
    """Raised when the configured CIDR cannot be parsed."""


class NetworkTooLargeError(DiscoveryRangeError):
    """Raised when a network exceeds the configured host limit."""

    def __init__(self, cidr: str, size: int, limit: int) -> None:
        self.cidr = cidr
        self.size = size
        self.limit = limit
        super().__init__(
            f"Network {cidr} is too large: {size} hosts exceed "
            f"the maximum of {limit} hosts"
        )


def count_hosts(cidr: str) -> int:
    """Number of usable host addresses in a CIDR range."""
    network = ipaddress.ip_network(cidr, strict=False)
    return max(network.num_addresses - 2, 0)


# Single source of truth for the TCP ports probed during network
# discovery and reused as the fallback probe list by monitoring.
FALLBACK_TCP_PORTS = [
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


@dataclass
class DiscoveredHost:
    ip_address: str
    hostname: str | None = None
    open_ports: list[int] = field(default_factory=list)
    reachable: bool = True


class NetworkScanner:
    """Parallel ICMP-first network scanner with TCP fallback.

    Each host is probed with ICMP echo when raw sockets are available;
    otherwise (or when ICMP gets no reply) a limited TCP probe over a
    predefined port list determines reachability. Probing runs in a
    bounded thread pool, never creating a thread per host.
    """

    DEFAULT_PORTS = FALLBACK_TCP_PORTS

    def __init__(
        self,
        timeout: float = 0.5,
        ports: list[int] | None = None,
        workers: int = 50,
        icmp_timeout: float = 1.0,
        max_hosts: int = 1024,
        icmp_probe: ICMPProbe | None = None,
    ) -> None:
        self.timeout = timeout
        self.workers = workers
        self.ports = ports if ports is not None else list(self.DEFAULT_PORTS)
        self.icmp_timeout = icmp_timeout
        self.max_hosts = max_hosts
        self._icmp_probe = icmp_probe or ICMPProbe(timeout=icmp_timeout)

    def scan_host(self, ip_address: str) -> DiscoveredHost | None:
        open_ports: list[int] = []

        if not self._probe_icmp(ip_address):
            open_ports = self._probe_tcp(ip_address)

            if not open_ports:
                return None

        hostname = self._resolve_hostname(ip_address)

        return DiscoveredHost(
            ip_address=ip_address,
            hostname=hostname,
            open_ports=open_ports,
            reachable=True,
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

        Raises ``DiscoveryRangeError`` for invalid or oversized ranges.
        """
        network = self._validate_range(cidr)
        addresses = [str(address) for address in network.hosts()]

        if len(addresses) > self.max_hosts:
            raise NetworkTooLargeError(cidr, len(addresses), self.max_hosts)

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

    def _probe_icmp(self, ip_address: str) -> bool:
        try:
            result = self._icmp_probe.probe(ip_address)
        except ICMPUnavailableError:
            return False

        return bool(result)

    def _probe_tcp(self, ip_address: str) -> list[int]:
        return [
            port
            for port in self.ports
            if self._is_port_open(ip_address, port)
        ]

    def _is_port_open(self, ip_address: str, port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                return sock.connect_ex((ip_address, port)) == 0
        except (OSError, socket.error):
            return False

    def _validate_range(self, cidr: str) -> ipaddress.IPv4Network:
        try:
            network = ipaddress.ip_network(cidr, strict=False)
        except ValueError as exc:
            raise InvalidCIDRError(f"Invalid CIDR: {cidr}") from exc

        size = max(network.num_addresses - 2, 0)

        if size > self.max_hosts:
            raise NetworkTooLargeError(cidr, size, self.max_hosts)

        return network

    @staticmethod
    def _resolve_hostname(ip_address: str) -> str | None:
        try:
            hostname, _, _ = socket.gethostbyaddr(ip_address)
            return hostname
        except (socket.herror, socket.gaierror, OSError):
            return None