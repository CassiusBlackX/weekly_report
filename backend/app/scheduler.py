"""APScheduler integration.

The `schedules` DB table is the single source of truth. On startup we load
all enabled rows into a background scheduler; add/update/delete/toggle in the
router calls sync_job()/remove_job() to keep the scheduler in step.

Each job, when it fires, opens the current reporting week (like an admin
clicking the button), so users can start filling in their reports.
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import settings
from .database import SessionLocal
from .models import Schedule
from .services import open_current_week

logger = logging.getLogger("weekly_report.scheduler")

_scheduler = BackgroundScheduler(timezone=settings.timezone)


def _job_id(schedule_id: int) -> str:
    return f"open_week_{schedule_id}"


def _run_open_week(schedule_id: int) -> None:
    db = SessionLocal()
    try:
        cycle = open_current_week(db, opened_by=None)
        logger.info("Schedule %s opened week %s", schedule_id, cycle.week_label)
    except Exception:  # pragma: no cover - defensive logging
        logger.exception("Schedule %s failed to open the week", schedule_id)
    finally:
        db.close()


def sync_job(schedule: Schedule) -> None:
    """Create/replace the APScheduler job for a schedule row (if enabled)."""
    job_id = _job_id(schedule.id)
    if not schedule.enabled:
        remove_job(schedule.id)
        return
    trigger = CronTrigger(
        day_of_week=schedule.day_of_week,
        hour=schedule.hour,
        minute=schedule.minute,
        timezone=settings.timezone,
    )
    _scheduler.add_job(
        _run_open_week,
        trigger=trigger,
        id=job_id,
        args=[schedule.id],
        replace_existing=True,
        misfire_grace_time=3600,
        coalesce=True,
    )


def remove_job(schedule_id: int) -> None:
    try:
        _scheduler.remove_job(_job_id(schedule_id))
    except Exception:
        pass


def start_scheduler() -> None:
    db = SessionLocal()
    try:
        for schedule in db.query(Schedule).filter(Schedule.enabled.is_(True)).all():
            sync_job(schedule)
    finally:
        db.close()
    if not _scheduler.running:
        _scheduler.start()
    logger.info("Scheduler started with %d job(s)", len(_scheduler.get_jobs()))


def shutdown_scheduler() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
