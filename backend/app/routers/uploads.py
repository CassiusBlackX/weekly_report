"""Image upload and authenticated serving.

Uploads are validated (declared type + actual image decode + size) and
stored under the data volume with a random filename. Serving requires a
valid session, so report images are not publicly accessible.
"""
import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from PIL import Image
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import csrf_protect, get_current_user
from ..models import Attachment, User

router = APIRouter(prefix="/uploads", tags=["uploads"])

_EXT_BY_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}


@router.post("")
async def upload_image(
    file: UploadFile = File(...),
    _: None = Depends(csrf_protect),
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if file.content_type not in settings.allowed_image_types:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "仅支持 JPG/PNG/GIF/WebP 图片")

    data = await file.read()
    if len(data) > settings.max_upload_bytes:
        mb = settings.max_upload_bytes // (1024 * 1024)
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"图片不能超过 {mb} MB")

    # Verify the bytes really are a decodable image of the declared kind.
    try:
        import io

        with Image.open(io.BytesIO(data)) as img:
            img.verify()
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "无效的图片文件")

    ext = _EXT_BY_TYPE[file.content_type]
    stored = f"{secrets.token_hex(16)}{ext}"
    dest: Path = settings.uploads_dir / stored
    dest.write_bytes(data)

    db.add(
        Attachment(
            stored_filename=stored,
            original_name=(file.filename or stored)[:255],
            uploader_id=current.id,
        )
    )
    db.commit()

    return {"url": f"{settings.base_path}/api/uploads/{stored}", "filename": stored}


@router.get("/{filename}")
def serve_image(filename: str, _: User = Depends(get_current_user)):
    # Resolve and confine to the uploads directory (anti path-traversal).
    target = (settings.uploads_dir / filename).resolve()
    if settings.uploads_dir.resolve() not in target.parents or not target.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "图片不存在")
    return FileResponse(target)
