"""Reporting cycles (weeks): listing, current week, open/close (admin)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import csrf_protect, get_current_user, require_admin
from ..models import ReportCycle, User
from ..schemas import CycleOut
from ..services import open_current_week
from ..week import current_week_bounds

router = APIRouter(prefix="/cycles", tags=["cycles"])


@router.get("", response_model=list[CycleOut])
def list_cycles(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(ReportCycle).order_by(ReportCycle.week_label.desc()).all()


@router.get("/current", response_model=CycleOut | None)
def get_current_cycle(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return the cycle for the current local week, or null if not opened yet."""
    label, _start, _end = current_week_bounds()
    return db.query(ReportCycle).filter(ReportCycle.week_label == label).one_or_none()


@router.post("/open-current", response_model=CycleOut)
def open_current(
    _: None = Depends(csrf_protect),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return open_current_week(db, opened_by=admin.id)


@router.post("/{cycle_id}/close", response_model=CycleOut)
def close_cycle(
    cycle_id: int,
    _: None = Depends(csrf_protect),
    __: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    cycle = db.get(ReportCycle, cycle_id)
    if cycle is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "周期不存在")
    cycle.is_open = False
    db.commit()
    db.refresh(cycle)
    return cycle
