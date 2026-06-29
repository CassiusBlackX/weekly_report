"""Pydantic request/response models."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---- Auth ----
class LoginIn(BaseModel):
    username: str
    password: str


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=128)


# ---- Users ----
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    display_name: str
    role: str
    is_active: bool
    created_at: datetime


class UserCreateIn(BaseModel):
    username: str = Field(min_length=2, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    display_name: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=6, max_length=128)
    role: str = Field(default="user", pattern=r"^(admin|user)$")


class UserUpdateIn(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=128)
    role: str | None = Field(default=None, pattern=r"^(admin|user)$")
    is_active: bool | None = None


class ResetPasswordIn(BaseModel):
    new_password: str = Field(min_length=6, max_length=128)


# ---- Cycles ----
class CycleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    week_label: str
    start_date: str
    end_date: str
    is_open: bool
    opened_at: datetime


# ---- Reports ----
class ReportSaveIn(BaseModel):
    content_html: str = ""
    content_json: str = ""


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    cycle_id: int
    user_id: int
    content_html: str
    content_json: str
    updated_at: datetime


class ReportWithUserOut(BaseModel):
    user_id: int
    username: str
    display_name: str
    report: ReportOut | None


# ---- Schedules ----
class ScheduleIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    day_of_week: int = Field(ge=0, le=6)
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)
    enabled: bool = True


class ScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    day_of_week: int
    hour: int
    minute: int
    enabled: bool
    created_at: datetime
