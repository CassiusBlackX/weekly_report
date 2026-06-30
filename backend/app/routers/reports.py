"""Weekly report viewing and editing.

Visibility: any logged-in user can view every active user's report for a
cycle. Editing: a user may only write their own report. The current week
can only be edited while its cycle is_open; past weeks are always editable
by their owner. Admins may delete reports to reclaim space.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import csrf_protect, get_current_user, require_admin
from ..images import cleanup_html_images, delete_files, filenames_in_html
from ..models import Report, ReportCycle, User
from ..sanitize import sanitize_html
from ..schemas import ReportOut, ReportSaveIn, ReportWithUserOut
from ..week import current_week_bounds

router = APIRouter(prefix="/reports", tags=["reports"])


def _get_cycle_or_404(db: Session, cycle_id: int) -> ReportCycle:
    cycle = db.get(ReportCycle, cycle_id)
    if cycle is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "周期不存在")
    return cycle


@router.get("/by-cycle/{cycle_id}", response_model=list[ReportWithUserOut])
def reports_by_cycle(
    cycle_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """All active reporting users alongside their report (or null) for this cycle.

    Admins are managers only and do not write reports, so they are excluded
    from the listing.
    """
    _get_cycle_or_404(db, cycle_id)
    users = (
        db.query(User)
        .filter(User.is_active.is_(True), User.role == "user")
        .order_by(User.display_name)
        .all()
    )
    reports = {
        r.user_id: r
        for r in db.query(Report).filter(Report.cycle_id == cycle_id).all()
    }
    return [
        ReportWithUserOut(
            user_id=u.id,
            username=u.username,
            display_name=u.display_name,
            report=ReportOut.model_validate(reports[u.id]) if u.id in reports else None,
        )
        for u in users
    ]


@router.put("/cycle/{cycle_id}", response_model=ReportOut)
def save_my_report(
    cycle_id: int,
    payload: ReportSaveIn,
    _: None = Depends(csrf_protect),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "管理员无需填写周报")

    cycle = _get_cycle_or_404(db, cycle_id)

    current_label, _s, _e = current_week_bounds()
    is_current_week = cycle.week_label == current_label
    if is_current_week and not cycle.is_open:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "本周填报尚未开启")

    clean_html = sanitize_html(payload.content_html)

    report = (
        db.query(Report)
        .filter(Report.cycle_id == cycle_id, Report.user_id == user.id)
        .one_or_none()
    )
    if report is None:
        report = Report(cycle_id=cycle_id, user_id=user.id)
        db.add(report)

    # Free images that were removed from the content during this edit.
    removed = filenames_in_html(report.content_html) - filenames_in_html(clean_html)
    delete_files(db, removed)

    report.content_html = clean_html
    report.content_json = payload.content_json
    db.commit()
    db.refresh(report)
    return report


@router.delete("/{report_id}")
def delete_report(
    report_id: int,
    _: None = Depends(csrf_protect),
    __: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin deletes a single report and its images (reclaim space)."""
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "周报不存在")
    cleanup_html_images(db, report.content_html)
    db.delete(report)
    db.commit()
    return {"ok": True}
