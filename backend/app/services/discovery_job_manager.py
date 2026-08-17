from __future__ import annotations

import ipaddress
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from flask import Flask

from app.extensions import db
from app.models.device import Device
from app.models.network import Network
from app.services.discovery_service import DiscoveryService
from app.services.network_scanner import DiscoveredHost, NetworkScanner


class DiscoveryJobError(Exception):
    """Base class for discovery job manager errors."""


class JobConflictError(DiscoveryJobError):
    """Raised when a new job cannot start because one is already running."""


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


@dataclass
class DiscoveryJob:
    """In-memory state of a discovery job for a single network."""

    network_id: int
    status: str = "running"
    phase: str = "scanning"
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
    total_hosts: int | None = None
    scanned_hosts: int = 0
    hosts_found: int | None = None
    devices_synced: int | None = None
    devices: list[dict[str, Any]] = field(default_factory=list)
    discovered_hosts: list[dict[str, Any]] = field(default_factory=list)
    _cancelled: bool = field(default=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    @property
    def progress(self) -> int:
        """Completion percentage, monotonic within ``0..100``."""
        total = self.total_hosts or 0

        if total <= 0:
            return 0

        return min(100, round(self.scanned_hosts / total * 100))

    def to_dict(self) -> dict[str, Any]:
        return {
            "network_id": self.network_id,
            "status": self.status,
            "phase": self.phase,
            "started_at": _iso(self.started_at),
            "finished_at": _iso(self.finished_at),
            "error": self.error,
            "total_hosts": self.total_hosts,
            "scanned_hosts": self.scanned_hosts,
            "hosts_found": self.hosts_found,
            "devices_synced": self.devices_synced,
            "discovered": len(self.discovered_hosts),
            "progress": self.progress,
            "devices": self.devices,
        }


class DiscoveryJobManager:
    """Run network discovery jobs in the background.

    Only one job may be active at a time (process-wide). Job state is
    kept in memory only — nothing is persisted on this stage, so under
    a single Gunicorn worker the state is consistent across requests.

    The manager follows the scheduler pattern: it is bound to the Flask
    app in ``create_app`` and worker threads run inside an application
    context. The scanner is injectable for tests.
    """

    SCAN_POLL_INTERVAL = 0.5

    def __init__(
        self,
        app: Flask | None = None,
        scanner: NetworkScanner | None = None,
    ) -> None:
        self._app = app
        self.scanner = scanner
        self._jobs: dict[int, DiscoveryJob] = {}
        self._active_network_id: int | None = None
        self._lock = threading.Lock()

    def init_app(self, app: Flask) -> None:
        self._app = app

    def start(self, network_id: int) -> DiscoveryJob:
        """Start a background discovery job for a network.

        Raises ``JobConflictError`` when another job is still running.
        """
        with self._lock:
            if self._active_network_id is not None:
                raise JobConflictError(
                    "A discovery job is already running for network "
                    f"{self._active_network_id}"
                )

            job = DiscoveryJob(
                network_id=network_id,
                status="running",
                phase="scanning",
                started_at=datetime.utcnow(),
            )
            self._jobs[network_id] = job
            self._active_network_id = network_id

        thread = threading.Thread(
            target=self._run_job,
            args=(job,),
            daemon=True,
        )
        thread.start()

        return job

    def status(self, network_id: int) -> DiscoveryJob | None:
        with self._lock:
            return self._jobs.get(network_id)

    def cancel(self, network_id: int) -> DiscoveryJob | None:
        """Request cancellation of a running job.

        A finished job is returned unchanged (cancel is idempotent).
        """
        with self._lock:
            job = self._jobs.get(network_id)

            if job is None:
                return None

            with job._lock:
                if job.status == "running":
                    job._cancelled = True
                    job.status = "cancelled"
                    job.phase = "cancelled"
                    job.finished_at = datetime.utcnow()

            return job

    def _run_job(self, job: DiscoveryJob) -> None:
        app = self._app

        try:
            if app is None:
                self._fail(job, "Discovery job manager is not bound to an application")
                return

            with app.app_context():
                network = db.session.get(Network, job.network_id)

                if network is None:
                    self._fail(job, "Network not found")
                    return

                job.total_hosts = self._count_hosts(network.cidr)

                scanner = self.scanner or NetworkScanner()
                hosts = self._scan(job, scanner, network.cidr)

                if hosts is None:
                    self._mark_cancelled(job)
                    return

                job.phase = "syncing"
                devices = DiscoveryService(network).sync_hosts(hosts)
                self._finish(job, hosts, devices)
        except Exception as exc:  # noqa: BLE001 — a background thread must never die silently
            self._fail(job, str(exc))
        finally:
            with self._lock:
                if self._active_network_id == job.network_id:
                    self._active_network_id = None

    def _scan(
        self,
        job: DiscoveryJob,
        scanner: NetworkScanner,
        cidr: str,
    ) -> list[DiscoveredHost] | None:
        """Run the scan while polling the cancel flag.

        Reports live progress via the scanner callback and returns
        ``None`` when the job was cancelled while scanning.
        """
        result: dict[str, list[DiscoveredHost]] = {"hosts": []}
        error: dict[str, str | None] = {"message": None}

        def run() -> None:
            try:
                result["hosts"] = scanner.scan_network(
                    cidr,
                    on_progress=self._on_progress(job),
                )
            except Exception as exc:  # noqa: BLE001 — surfaced through `error`
                error["message"] = str(exc)

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

        while thread.is_alive():
            if job._cancelled:
                return None
            thread.join(self.SCAN_POLL_INTERVAL)

        if error["message"] is not None:
            raise RuntimeError(error["message"])

        return result["hosts"]

    @staticmethod
    def _on_progress(job: DiscoveryJob) -> Callable[[int, DiscoveredHost | None], None]:
        def on_progress(scanned: int, host: DiscoveredHost | None) -> None:
            with job._lock:
                if job._cancelled:
                    return
                job.scanned_hosts = max(job.scanned_hosts, scanned)
                if host is not None:
                    job.discovered_hosts.append(DiscoveryJobManager._host_to_result(host))

        return on_progress

    @staticmethod
    def _host_to_result(host: DiscoveredHost) -> dict[str, Any]:
        return {
            "ip_address": host.ip_address,
            "hostname": host.hostname,
            "open_ports": host.open_ports,
            "reachable": bool(host.open_ports),
            "device_id": None,
        }

    def _finish(
        self,
        job: DiscoveryJob,
        hosts: list[DiscoveredHost],
        devices: list[Device],
    ) -> None:
        with job._lock:
            if job._cancelled:
                self._mark_cancelled_locked(job)
                return

            job.scanned_hosts = job.total_hosts or 0
            job.hosts_found = len(hosts)
            job.devices_synced = len(devices)
            job.discovered_hosts = [
                {
                    **self._host_to_result(host),
                    "device_id": device.id,
                }
                for host, device in zip(hosts, devices)
            ]
            job.devices = [
                {
                    "id": device.id,
                    "name": device.name,
                    "hostname": device.hostname,
                    "device_type": device.device_type,
                }
                for device in devices
            ]
            job.status = "completed"
            job.phase = "done"
            job.finished_at = datetime.utcnow()

    def _mark_cancelled(self, job: DiscoveryJob) -> None:
        with job._lock:
            self._mark_cancelled_locked(job)

    @staticmethod
    def _mark_cancelled_locked(job: DiscoveryJob) -> None:
        if job.status == "running":
            job._cancelled = True
            job.status = "cancelled"
            job.phase = "cancelled"
            job.finished_at = datetime.utcnow()

    def _fail(self, job: DiscoveryJob, message: str) -> None:
        with job._lock:
            job.status = "failed"
            job.phase = "done"
            job.error = message
            job.finished_at = datetime.utcnow()

    @staticmethod
    def _count_hosts(cidr: str) -> int:
        network = ipaddress.ip_network(cidr, strict=False)
        return max(network.num_addresses - 2, 0)
