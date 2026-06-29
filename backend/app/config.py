"""Application configuration loaded from environment variables.

All settings have sane defaults for local development. In production
(the Podman container) SECRET_KEY and the admin bootstrap credentials
should always be provided explicitly.
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # URL prefix the whole app is mounted under (matches nginx location).
    base_path: str = "/weekly_report"

    # Signing key for session cookies. MUST be overridden in production.
    secret_key: str = "dev-insecure-change-me"

    # Where SQLite db and uploaded images live (a mounted volume in prod).
    data_dir: Path = Path("./data")

    # Directory holding the built React app (copied in by the Dockerfile).
    frontend_dist: Path = Path("./frontend_dist")

    # Timezone for week calculation and scheduled jobs.
    timezone: str = "Asia/Shanghai"

    # Initial admin bootstrap (created on first start only if no admin exists).
    admin_username: str = "admin"
    admin_password: str = "changeme"

    # Auth / brute-force protection.
    session_max_age_seconds: int = 7 * 24 * 3600  # 7 days
    max_failed_attempts: int = 3
    lockout_minutes: int = 10
    # Set False for local http development so the cookie is sent over http.
    cookie_secure: bool = True

    # Upload limits.
    max_upload_bytes: int = 10 * 1024 * 1024  # 10 MB per image
    allowed_image_types: tuple[str, ...] = (
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
    )

    @property
    def db_path(self) -> Path:
        return self.data_dir / "app.db"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.db_path}"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    return settings


settings = get_settings()
