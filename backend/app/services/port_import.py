"""Source-agnostic mass import for service ports.

Accepts a normalized list of :class:`ImportItem` (device reference +
port/protocol + optional display name) and upserts the missing
``Port``/``Service`` records into the inventory without touching
manually edited data.

The service is intentionally independent of any concrete source:
Docker, Proxmox, Nmap, MikroTik and hand-written lists all reduce to
the same ``ImportItem`` contract before calling :meth:`PortImportService.sync`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.extensions import db
from app.models.device import Device
from app.models.interface import Interface
from app.models.ip_address import IPAddress
from app.models.port import Port
from app.models.service import Service
from app.web.helpers import port_service_name

# Only ports whose web nature is unambiguous get a ``web_scheme`` and
# therefore a ``web_url``. Unknown services are never given an invented
# URL.
WEB_PORT_SCHEMES: dict[tuple[int, str], str] = {
    (80, "tcp"): "http",
    (443, "tcp"): "https",
    (3000, "tcp"): "http",
    (8000, "tcp"): "http",
    (8006, "tcp"): "https",
    (8080, "tcp"): "http",
    (8088, "tcp"): "http",
    (8443, "tcp"): "https",
    (9443, "tcp"): "https",
}


@dataclass
class ImportItem:
    """One normalized port import record.

    ``device`` may be an integer id or a string that resolves to a
    device (IP address first, then name/hostname).
    """

    device: int | str
    port_number: int
    protocol: str
    display_name: str | None = None
    description: str | None = None


@dataclass
class ImportResult:
    """Outcome of one import run."""

    created: list[dict] = field(default_factory=list)
    updated: list[dict] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "created": self.created,
            "updated": self.updated,
            "skipped": self.skipped,
            "summary": {
                "created": len(self.created),
                "updated": len(self.updated),
                "skipped": len(self.skipped),
            },
        }


class PortImportService:
    """Upsert ports/services from a normalized import list."""

    def sync(self, items: list[ImportItem]) -> ImportResult:
        result = ImportResult()

        for item in items:
            self._sync_item(item, result)

        db.session.commit()
        return result

    def _sync_item(self, item: ImportItem, result: ImportResult) -> None:
        device = self._resolve_device(item.device)

        if device is None:
            result.skipped.append(self._record(item, reason="device not found"))
            return

        if item.protocol not in {"tcp", "udp"}:
            result.skipped.append(
                self._record(item, reason="unsupported protocol")
            )
            return

        existing = Port.query.filter_by(
            device_id=device.id,
            port_number=item.port_number,
            protocol=item.protocol,
        ).first()

        if existing is not None:
            # Never overwrite manual data. Only re-activate the port and
            # backfill a display name when none was set by hand.
            changed = False

            if existing.status != "open":
                existing.status = "open"
                changed = True

            if not (existing.display_name or "").strip():
                existing.display_name = item.display_name
                changed = True

            if changed:
                result.updated.append(self._record(item, device=device))
            else:
                result.skipped.append(
                    self._record(item, device=device, reason="already exists")
                )
            return

        service_id = None

        if item.display_name:
            service = Service.query.filter_by(name=item.display_name).first()

            if service is None:
                service = Service(name=item.display_name)
                db.session.add(service)
                db.session.flush()

            service_id = service.id

        description = self._build_description(item)

        port = Port(
            device_id=device.id,
            service_id=service_id,
            port_number=item.port_number,
            protocol=item.protocol,
            status="open",
            display_name=item.display_name,
            web_scheme=WEB_PORT_SCHEMES.get((item.port_number, item.protocol)),
            description=description,
        )
        db.session.add(port)
        result.created.append(self._record(item, device=device))

    def _resolve_device(self, reference: int | str) -> Device | None:
        if isinstance(reference, int):
            return db.session.get(Device, reference)

        text = str(reference).strip()

        if not text:
            return None

        ip_address = (
            IPAddress.query
            .join(Interface)
            .filter(IPAddress.address == text)
            .first()
        )

        if ip_address is not None:
            return ip_address.interface.device

        return (
            Device.query
            .filter(
                (Device.name == text)
                | (Device.hostname == text)
            )
            .first()
        )

    @staticmethod
    def _build_description(item: ImportItem) -> str | None:
        """Build a description that tags the port as auto-imported.

        The leading ``import:`` marker lets operators distinguish
        inventory that came from a mass import from hand-added records
        without a schema migration.
        """
        parts = ["import:auto"]

        if item.description:
            parts.append(item.description)

        return " ".join(parts)

    @staticmethod
    def _record(
        item: ImportItem,
        device: Device | None = None,
        reason: str | None = None,
    ) -> dict:
        record = {
            "device_id": device.id if device else None,
            "device": str(item.device),
            "port": item.port_number,
            "protocol": item.protocol,
            "display_name": item.display_name,
            "web_scheme": WEB_PORT_SCHEMES.get(
                (item.port_number, item.protocol)
            ),
        }

        if reason:
            record["reason"] = reason

        return record