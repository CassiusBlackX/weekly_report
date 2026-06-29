"""Admin-managed weekly schedules that auto-open the reporting week.

At most 10 schedules may exist. Each can be enabled/disabled like an alarm.
The scheduler module keeps APScheduler jobs in sync with these rows.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import csrf_protect, require_admin
from ..models import Schedule, User
from ..schemas import ScheduleIn, ScheduleOut
from ..scheduler import remove_job, sync_job

router = APIRouter(prefix="/schedules", tags=["schedules"])

MAX_SCHEDULES = 10


@router.get("", response_model=list[ScheduleOut])
def list_schedules(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(Schedule).order_by(Schedule.id).all()


@router.post("", response_model=ScheduleOut, status_code=status.HTTP_201_CREATED)
def create_schedule(
    payload: ScheduleIn,
    _: None = Depends(csrf_protect),
    __: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if db.query(Schedule).count() >= MAX_SCHEDULES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"最多只能创建 {MAX_SCHEDULES} 个定时任务")
    schedule = Schedule(**payload.model_dump())
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    sync_job(schedule)
    return schedule


@router.put("/{schedule_id}", response_model=ScheduleOut)
def update_schedule(
    schedule_id: int,
    payload: ScheduleIn,
    _: None = Depends(csrf_protect),
    __: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    schedule = db.get(Schedule, schedule_id)
    if schedule is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "定时任务不存在")
    for field, value in payload.model_dump().items():
        setattr(schedule, field, value)
    db.commit()
    db.refresh(schedule)
    sync_job(schedule)
    return schedule


@router.post("/{schedule_id}/toggle", response_model=ScheduleOut)
def toggle_schedule(
    schedule_id: int,
    _: None = Depends(csrf_protect),
    __: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    schedule = db.get(Schedule, schedule_id)
    if schedule is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "定时任务不存在")
    schedule.enabled = not schedule.enabled
    db.commit()
    db.refresh(schedule)
    sync_job(schedule)
    return schedule


@router.delete("/{schedule_id}")
def delete_schedule(
    schedule_id: int,
    _: None = Depends(csrf_protect),
    __: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    schedule = db.get(Schedule, schedule_id)
    if schedule is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "定时任务不存在")
    db.delete(schedule)
    db.commit()
    remove_job(schedule_id)
    return {"ok": True}
