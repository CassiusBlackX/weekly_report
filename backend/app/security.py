"""Password hashing, signed session tokens and CSRF helpers."""
import secrets

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from passlib.context import CryptContext

from .config import settings

_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
_serializer = URLSafeTimedSerializer(settings.secret_key, salt="weekly-report-session")

SESSION_COOKIE = "wr_session"
CSRF_COOKIE = "wr_csrf"
CSRF_HEADER = "x-csrf-token"


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _pwd_context.verify(password, password_hash)
    except Exception:
        return False


def create_session_token(user_id: int) -> str:
    return _serializer.dumps({"uid": user_id})


def read_session_token(token: str) -> int | None:
    """Return the user id encoded in a valid, unexpired token, else None."""
    try:
        data = _serializer.loads(token, max_age=settings.session_max_age_seconds)
    except (BadSignature, SignatureExpired):
        return None
    uid = data.get("uid")
    return uid if isinstance(uid, int) else None


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)
