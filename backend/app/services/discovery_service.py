from __future__ import annotations

from app.extensions import db
from app.models.device import Device
from app.models.interface import Interface
from app.models.ip_address import IPAddress
from app.models.network import Network
from app.models.port import Port
from app.services.network_scanner import DiscoveredHost


class DiscoveryService:
    """Synchronize discovered network hosts with the database."""

    def __init__(self, network: Network) -> None:
        self.network = network

    def sync_hosts(
        self,
        hosts: list[DiscoveredHost],
    ) -> list[Device]:
        devices: list[Device] = []

        for host in hosts:
            device = self._sync_host(host)
            devices.append(device)

        discovered_ip_addresses = {
            host.ip_address
            for host in hosts
        }

        self._mark_missing_devices_inactive(
            discovered_ip_addresses
        )

        db.session.commit()

        return devices

    def _sync_host(self, host: DiscoveredHost) -> Device:
        ip_address = self._find_ip_address(host.ip_address)

        if ip_address is not None:
            interface = ip_address.interface
            device = interface.device
        else:
            device = self._find_device(host)

            if device is None:
                device = Device(
                    network_id=self.network.id,
                    name=host.hostname or host.ip_address,
                    hostname=host.hostname,
                    device_type="unknown",
                    is_active=True,
                )
                db.session.add(device)
                db.session.flush()

            interface = self._get_or_create_interface(device)

            ip_address = IPAddress(
                interface_id=interface.id,
                address=host.ip_address,
                version=4,
                is_primary=True,
            )
            db.session.add(ip_address)

        self._update_device(device, host)
        self._sync_ports(device, host)

        return device

    def _find_ip_address(self, address: str) -> IPAddress | None:
        return (
            IPAddress.query
            .join(Interface)
            .join(Device)
            .filter(
                IPAddress.address == address,
                Device.network_id == self.network.id,
            )
            .first()
        )

    def _find_device(self, host: DiscoveredHost) -> Device | None:
        # First try to identify the device by its IP address.
        ip_address = self._find_ip_address(host.ip_address)

        if ip_address is not None:
            return ip_address.interface.device

        # If the IP is not known yet, try hostname.
        if host.hostname:
            device = (
                Device.query
                .filter(
                    Device.network_id == self.network.id,
                    Device.hostname == host.hostname,
                )
                .first()
            )

            if device is not None:
                return device

        return None

    @staticmethod
    def _get_or_create_interface(device: Device) -> Interface:
        interface = (
            Interface.query
            .filter_by(
                device_id=device.id,
                name="discovered",
            )
            .first()
        )

        if interface is None:
            interface = Interface(
                device_id=device.id,
                name="discovered",
                interface_type="unknown",
                is_active=True,
            )
            db.session.add(interface)
            db.session.flush()

        return interface

    @staticmethod
    def _update_device(
        device: Device,
        host: DiscoveredHost,
    ) -> None:
        device.is_active = True

        if host.hostname:
            device.hostname = host.hostname

            if device.name.startswith("192.168."):
                device.name = host.hostname

    @staticmethod
    def _sync_ports(
        device: Device,
        host: DiscoveredHost,
    ) -> None:
        existing_ports = {
            (port.port_number, port.protocol): port
            for port in device.ports
        }

        for port_number in host.open_ports:
            key = (port_number, "tcp")

            port = existing_ports.get(key)

            if port is None:
                port = Port(
                    device_id=device.id,
                    port_number=port_number,
                    protocol="tcp",
                    status="open",
                )
                db.session.add(port)
            else:
                port.status = "open"

    def _mark_missing_devices_inactive(
        self,
        discovered_ip_addresses: set[str],
    ) -> None:
        devices = (
            Device.query
            .filter_by(network_id=self.network.id)
            .all()
        )

        for device in devices:
            ip_addresses = {
                ip.address
                for interface in device.interfaces
                for ip in interface.ip_addresses
            }

            if ip_addresses and ip_addresses.isdisjoint(
                discovered_ip_addresses
            ):
                device.is_active = False
