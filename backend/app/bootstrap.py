"""First-run bootstrap: ensure an initial admin account exists."""
import logging

from .config import settings
from .database import SessionLocal
from .models import User
from .security import hash_password

logger = logging.getLogger("weekly_report.bootstrap")


def ensure_admin() -> None:
    db = SessionLocal()
    try:
        has_admin = db.query(User).filter(User.role == "admin").first() is not None
        if has_admin:
            return
        admin = User(
            username=settings.admin_username,
            display_name="管理员",
            password_hash=hash_password(settings.admin_password),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        logger.warning(
            "Bootstrapped initial admin '%s'. Change the password after first login.",
            settings.admin_username,
        )
    finally:
        db.close()
