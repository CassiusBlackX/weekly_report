"""ISO-week helpers computed in the configured local timezone."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .config import settings

_TZ = ZoneInfo(settings.timezone)


def current_local_date() -> datetime:
    return datetime.now(_TZ)


def week_bounds(dt: datetime) -> tuple[str, str, str]:
    """Return (week_label, start_date, end_date) for the ISO week of dt.

    week_label looks like '2026-W27'; start is Monday, end is Sunday,
    both as ISO 'YYYY-MM-DD' strings.
    """
    iso_year, iso_week, iso_weekday = dt.isocalendar()
    monday = dt.date() - timedelta(days=iso_weekday - 1)
    sunday = monday + timedelta(days=6)
    label = f"{iso_year}-W{iso_week:02d}"
    return label, monday.isoformat(), sunday.isoformat()


def current_week_bounds() -> tuple[str, str, str]:
    return week_bounds(current_local_date())
