"""Authentication: login, logout, current-user, change-password.

Brute-force protection: a user's failed_count increments on each bad
attempt; reaching max_failed_attempts locks the account for lockout_minutes.
Error messages are deliberately generic to avoid user enumeration.
"""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import csrf_protect, get_current_user
from ..models import User, utcnow
from ..schemas import ChangePasswordIn, LoginIn, UserOut
from ..security import (
    CSRF_COOKIE,
    SESSION_COOKIE,
    create_session_token,
    hash_password,
    new_csrf_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_GENERIC_ERROR = "用户名或密码错误"


def _set_auth_cookies(response: Response, user_id: int) -> None:
    token = create_session_token(user_id)
    csrf = new_csrf_token()
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.session_max_age_seconds,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path=settings.base_path,
    )
    response.set_cookie(
        CSRF_COOKIE,
        csrf,
        max_age=settings.session_max_age_seconds,
        httponly=False,  # readable by JS so it can echo into the X-CSRF-Token header
        secure=settings.cookie_secure,
        samesite="lax",
        path=settings.base_path,
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path=settings.base_path)
    response.delete_cookie(CSRF_COOKIE, path=settings.base_path)


@router.post("/login", response_model=UserOut)
def login(payload: LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).one_or_none()

    now = utcnow()
    # Locked accounts are rejected before any password check.
    if user and user.locked_until and user.locked_until > now:
        remaining = int((user.locked_until - now).total_seconds() // 60) + 1
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, f"账号已锁定，请 {remaining} 分钟后再试")

    if user is None or not verify_password(payload.password, user.password_hash):
        if user is not None:
            user.failed_count += 1
            if user.failed_count >= settings.max_failed_attempts:
                user.locked_until = now + timedelta(minutes=settings.lockout_minutes)
                user.failed_count = 0
            db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, _GENERIC_ERROR)

    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "账号已被停用")

    # Success: reset brute-force counters and issue cookies.
    user.failed_count = 0
    user.locked_until = None
    db.commit()
    _set_auth_cookies(response, user.id)
    return user


@router.post("/logout")
def logout(response: Response, _: None = Depends(csrf_protect), user: User = Depends(get_current_user)):
    _clear_auth_cookies(response)
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/change-password")
def change_password(
    payload: ChangePasswordIn,
    _: None = Depends(csrf_protect),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "原密码错误")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"ok": True}
