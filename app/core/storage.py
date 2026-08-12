import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings

_EXT_BY_CONTENT_TYPE = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


async def save_upload(file: UploadFile, *, subfolder: str) -> tuple[str, str]:
    """Persists an uploaded file under UPLOADS_DIR/<subfolder> and returns (url, content_type)."""
    content_type = file.content_type or "application/octet-stream"
    ext = Path(file.filename or "").suffix.lower()
    if not ext:
        ext = _EXT_BY_CONTENT_TYPE.get(content_type, "")

    folder = Path(settings.UPLOADS_DIR) / subfolder
    folder.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{ext}"
    destination = folder / filename
    destination.write_bytes(await file.read())

    return f"/uploads/{subfolder}/{filename}", content_type
