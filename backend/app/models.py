"""SQLAlchemy ORM models.

Schema is created with Base.metadata.create_all on startup (see main.py).
For a single-file SQLite DB serving ~20 users this is simpler than running
Alembic migrations; migrations can be layered on later if the schema grows.
"""
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    # Naive UTC: SQLite DateTime columns are timezone-naive, so keeping all
    # stored/compared values naive avoids "offset-naive vs offset-aware" errors.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(16), default="user", nullable=False)  # 'admin' | 'user'
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    # Brute-force protection state.
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    reports: Mapped[list["Report"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


class ReportCycle(Base):
    """A single week's reporting cycle. Created/opened by an admin."""

    __tablename__ = "report_cycles"

    id: Mapped[int] = mapped_column(primary_key=True)
    week_label: Mapped[str] = mapped_column(String(16), unique=True, index=True, nullable=False)  # e.g. 2026-W27
    start_date: Mapped[str] = mapped_column(String(10), nullable=False)  # ISO date (local week Monday)
    end_date: Mapped[str] = mapped_column(String(10), nullable=False)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    opened_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    reports: Mapped[list["Report"]] = relationship(back_populates="cycle", cascade="all, delete-orphan")


class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (UniqueConstraint("cycle_id", "user_id", name="uq_report_cycle_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    cycle_id: Mapped[int] = mapped_column(ForeignKey("report_cycles.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content_html: Mapped[str] = mapped_column(Text, default="", nullable=False)
    content_json: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    cycle: Mapped["ReportCycle"] = relationship(back_populates="reports")
    user: Mapped["User"] = relationship(back_populates="reports")


class Attachment(Base):
    """Bookkeeping for uploaded images stored on the data volume."""

    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    stored_filename: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    uploader_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class Schedule(Base):
    """A weekly cron entry that auto-opens the current reporting week.

    Acts like a phone alarm: enabled can be toggled without deleting it.
    A hard cap of 10 rows is enforced in the router.
    """

    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Mon .. 6=Sun
    hour: Mapped[int] = mapped_column(Integer, nullable=False)
    minute: Mapped[int] = mapped_column(Integer, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
