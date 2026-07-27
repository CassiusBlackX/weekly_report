"""FastAPI dependencies: current user resolution, role checks, CSRF guard."""
import secrets

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User
from .security import (
    CSRF_COOKIE,
    CSRF_HEADER,
    SESSION_COOKIE,
    hash_password,
    new_csrf_token,
    read_session_token,
)

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def _decode_header_utf8(value: str | None) -> str | None:
    """Starlette decodes header values as latin1 (one byte per char), per
    historical HTTP spec assumptions — a non-ASCII value like a Chinese
    display name arrives as mojibake unless re-decoded as the UTF-8 it
    actually is. Re-encoding back to latin1 bytes recovers the original
    wire bytes exactly (latin1 is a 1:1 byte<->codepoint mapping for 0-255).
    """
    if not value:
        return value
    return value.encode("latin-1").decode("utf-8")


def _get_or_create_sso_user(db: Session, username: str, display_name: str | None) -> User:
    """Resolve the identity nginx/Authelia already verified (Remote-User
    header). This process is bound to 127.0.0.1 and only reachable through
    nginx's auth_request gate, which always overwrites any client-supplied
    copy of this header before forwarding, so its presence here is
    authoritative and cannot be spoofed by the browser. JIT-provisions a
    local row on first sight so the SSO gateway alone is enough to log in —
    the password-based /auth/login flow below stays as an unreachable
    fallback (this app is never reachable except through that gate).
    """
    # Case-insensitive: lldap normalizes every uid to lowercase regardless
    # of how it was typed at creation, but a pre-seeded row (e.g. the
    # bootstrap admin, created from the ADMIN_USERNAME env var as typed at
    # deploy time) may still have mixed case. Match either way so the
    # bootstrap admin row and the SSO login for the same person resolve to
    # the same row instead of silently creating a second, non-admin one.
    user = db.query(User).filter(func.lower(User.username) == username).one_or_none()
    if user is not None:
        if display_name and display_name != user.display_name:
            user.display_name = display_name
            db.commit()
        return user
    user = User(
        username=username,
        display_name=display_name or username,
        password_hash=hash_password(secrets.token_urlsafe(32)),
        role="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_current_user(request: Request, response: Response, db: Session = Depends(get_db)) -> User:
    sso_username = request.headers.get("remote-user")
    if sso_username:
        sso_username = sso_username.lower()
        display_name = _decode_header_utf8(request.headers.get("remote-name"))
        user = _get_or_create_sso_user(db, sso_username, display_name)
        # The frontend's double-submit CSRF check needs a wr_csrf cookie to
        # echo back; the SSO path never runs the /auth/login flow that
        # normally issues one, so hand one out here on first sight.
        if not request.cookies.get(CSRF_COOKIE):
            response.set_cookie(
                CSRF_COOKIE,
                new_csrf_token(),
                max_age=settings.session_max_age_seconds,
                httponly=False,
                secure=settings.cookie_secure,
                samesite="lax",
                path=settings.base_path,
            )
        return user

    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "未登录")
    uid = read_session_token(token)
    if uid is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "会话已过期，请重新登录")
    user = db.get(User, uid)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "账号不可用")
    return user


def is_sso_request(request: Request) -> bool:
    """Whether this request was authenticated via the SSO gateway (nginx
    always sets Remote-User after Authelia's auth_request passes) rather
    than this app's own session cookie."""
    return bool(request.headers.get("remote-user"))


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "需要管理员权限")
    return user


def csrf_protect(request: Request) -> None:
    """Double-submit-cookie CSRF check for state-changing requests."""
    if request.method in _SAFE_METHODS:
        return
    cookie = request.cookies.get(CSRF_COOKIE)
    header = request.headers.get(CSRF_HEADER)
    if not cookie or not header or cookie != header:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "CSRF 校验失败")
