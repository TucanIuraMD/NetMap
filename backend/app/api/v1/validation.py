"""Shared field validation helpers for the REST API layer.

Keeps validation rules in one place so API modules (and future
service code) behave consistently. All helpers return ``(value, error)``
where ``error`` is None when the value is acceptable.
"""

from __future__ import annotations

import ipaddress
import re

INTERFACE_TYPES = {
    "ethernet",
    "wireless",
    "virtual",
    "bridge",
    "vlan",
    "bond",
    "tunnel",
    "other",
}

PORT_PROTOCOLS = {"tcp", "udp"}
PORT_STATUSES = {"open", "closed", "filtered", "unknown"}

_MAC_RE = re.compile(r"^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$")


def validate_interface_type(value: str | None) -> tuple[str | None, str | None]:
    if value is None:
        return None, None

    if value not in INTERFACE_TYPES:
        return value, (
            "interface_type must be one of: "
            + ", ".join(sorted(INTERFACE_TYPES))
        )

    return value, None


def validate_mac_address(value: str | None) -> tuple[str | None, str | None]:
    if value is None:
        return None, None

    if not _MAC_RE.match(value):
        return value, "mac_address must look like aa:bb:cc:dd:ee:ff"

    return value, None


def validate_positive_int(
    value,
    label: str,
) -> tuple[int | None, str | None]:
    if value is None:
        return None, None

    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        return None, f"{label} must be a positive integer"

    return value, None


def validate_ip_address(
    address: str | None,
    version: int | None,
) -> tuple[str | int | None, str | None]:
    if address is None:
        return address, "address is required"

    try:
        parsed = ipaddress.ip_address(address.strip())
    except ValueError:
        return address, f"'{address}' is not a valid IPv4/IPv6 address"

    if version not in (4, 6):
        return address, "version must be 4 or 6"

    expected = parsed.version

    if version != expected:
        return address, (
            f"version {version} does not match address family "
            f"(address is IPv{expected})"
        )

    return address.strip(), None


def validate_port_number(value) -> tuple[int | None, str | None]:
    if value is None:
        return None, "port_number is required"

    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 1 <= value <= 65535
    ):
        return None, "port_number must be an integer between 1 and 65535"

    return value, None


def validate_port_protocol(value: str | None) -> tuple[str | None, str | None]:
    if value is None:
        return None, "protocol is required"

    normalized = value.lower()

    if normalized not in PORT_PROTOCOLS:
        return value, "protocol must be tcp or udp"

    return normalized, None


def validate_port_status(value: str | None) -> tuple[str | None, str | None]:
    if value is None:
        return None, None

    if value not in PORT_STATUSES:
        return value, (
            "status must be one of: " + ", ".join(sorted(PORT_STATUSES))
        )

    return value, None