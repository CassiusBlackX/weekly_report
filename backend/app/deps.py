"""FastAPI dependencies: current user resolution, role checks, CSRF guard."""
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .security import CSRF_COOKIE, CSRF_HEADER, SESSION_COOKIE, read_session_token

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
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
