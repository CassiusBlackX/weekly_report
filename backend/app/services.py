"""Domain operations shared between HTTP routers and the scheduler."""
from sqlalchemy.orm import Session

from .models import ReportCycle
from .week import current_week_bounds


def open_current_week(db: Session, opened_by: int | None = None) -> ReportCycle:
    """Create (or re-open) the reporting cycle for the current local week.

    Idempotent: calling it repeatedly for the same week just ensures the
    existing cycle is open. Returns the cycle.
    """
    label, start, end = current_week_bounds()
    cycle = db.query(ReportCycle).filter(ReportCycle.week_label == label).one_or_none()
    if cycle is None:
        cycle = ReportCycle(
            week_label=label,
            start_date=start,
            end_date=end,
            is_open=True,
            opened_by=opened_by,
        )
        db.add(cycle)
    else:
        cycle.is_open = True
        if opened_by is not None:
            cycle.opened_by = opened_by
    db.commit()
    db.refresh(cycle)
    return cycle
