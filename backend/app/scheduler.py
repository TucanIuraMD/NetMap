from __future__ import annotations

from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler


def _monitoring_job(app: Flask) -> None:
    from app.services.monitoring_service import MonitoringService

    with app.app_context():
        result = MonitoringService().check_all()
        app.logger.info("Monitoring run: %s", result)


def init_scheduler(app: Flask) -> BackgroundScheduler:
    """Create and start the application-wide background scheduler.

    The scheduler must run exactly once per worker process. Under the
    Flask debug reloader, ``create_app`` is executed in both the parent
    monitor process and the child worker, so callers are responsible
    for applying the reloader guard (see ``should_start_scheduler``).
    """
    scheduler = BackgroundScheduler(
        daemon=True,
        job_defaults={
            "coalesce": True,
            "max_instances": 1,
        },
    )

    scheduler.add_job(
        _monitoring_job,
        args=[app],
        trigger="interval",
        minutes=app.config["MONITORING_INTERVAL_MINUTES"],
        id="netmap-monitoring",
        replace_existing=True,
    )

    scheduler.start()
    return scheduler


def should_start_scheduler(app: Flask) -> bool:
    if not app.config.get("MONITORING_ENABLED", True):
        return False

    if app.debug:
        # The debug reloader runs the app in two processes; only the
        # real worker sets WERKZEUG_RUN_MAIN. Starting the scheduler in
        # the parent too would duplicate every periodic job.
        import os

        return os.environ.get("WERKZEUG_RUN_MAIN") == "true"

    return True