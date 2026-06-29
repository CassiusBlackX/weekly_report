"""User management (admin only) and the active-users listing.

All authenticated users can list active users (to browse their reports).
Creating, updating, deleting and password resets require admin.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import csrf_protect, get_current_user, require_admin
from ..models import User
from ..schemas import ResetPasswordIn, UserCreateIn, UserOut, UserUpdateIn
from ..security import hash_password

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(
    include_inactive: bool = False,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Only admins may see inactive (deleted) users.
    show_inactive = include_inactive and current.is_admin
    query = db.query(User)
    if not show_inactive:
        query = query.filter(User.is_active.is_(True))
    return query.order_by(User.display_name).all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateIn,
    _: None = Depends(csrf_protect),
    __: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "用户名已存在")
    user = User(
        username=payload.username,
        display_name=payload.display_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdateIn,
    _: None = Depends(csrf_protect),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
    if payload.display_name is not None:
        user.display_name = payload.display_name
    if payload.role is not None:
        if user.id == admin.id and payload.role != "admin":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "不能取消自己的管理员身份")
        user.role = payload.role
    if payload.is_active is not None:
        if user.id == admin.id and not payload.is_active:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "不能停用自己")
        user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/reset-password")
def reset_password(
    user_id: int,
    payload: ResetPasswordIn,
    _: None = Depends(csrf_protect),
    __: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
    user.password_hash = hash_password(payload.new_password)
    user.failed_count = 0
    user.locked_until = None
    db.commit()
    return {"ok": True}


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    _: None = Depends(csrf_protect),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Permanently delete a user and (via cascade) all their reports."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
    if user.id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "不能删除自己")
    db.delete(user)
    db.commit()
    return {"ok": True}
