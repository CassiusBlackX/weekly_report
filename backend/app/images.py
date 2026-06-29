"""Helpers for locating and deleting uploaded image files.

Images are referenced inside report HTML as
    {base_path}/api/uploads/{stored_filename}
When a report or whole cycle is deleted we extract those filenames and
remove the files from the data volume plus their attachment rows, so disk
space is actually reclaimed.
"""
import re

from sqlalchemy.orm import Session

from .config import settings
from .models import Attachment

_UPLOAD_REF = re.compile(
    re.escape(f"{settings.base_path}/api/uploads/") + r"([A-Za-z0-9_.\-]+)"
)


def filenames_in_html(html: str) -> set[str]:
    return set(_UPLOAD_REF.findall(html or ""))


def delete_files(db: Session, filenames: set[str]) -> int:
    """Delete given uploaded files from disk and their attachment rows."""
    removed = 0
    for name in filenames:
        # Guard against path traversal even though the regex is restrictive.
        safe = (settings.uploads_dir / name).resolve()
        if settings.uploads_dir.resolve() not in safe.parents:
            continue
        if safe.exists():
            safe.unlink()
            removed += 1
    if filenames:
        db.query(Attachment).filter(Attachment.stored_filename.in_(filenames)).delete(
            synchronize_session=False
        )
    return removed


def cleanup_html_images(db: Session, html: str) -> int:
    return delete_files(db, filenames_in_html(html))
