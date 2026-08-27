import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings

_EXT_BY_CONTENT_TYPE = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
    "video/webm": ".webm",
}


async def save_upload(
    file: UploadFile, *, subfolder: str, max_size_bytes: int | None = None
) -> tuple[str, str]:
    """Persists an uploaded file under UPLOADS_DIR/<subfolder> and returns (url, content_type)."""
    content_type = file.content_type or "application/octet-stream"
    ext = Path(file.filename or "").suffix.lower()
    if not ext:
        ext = _EXT_BY_CONTENT_TYPE.get(content_type, "")

    data = await file.read()
    if max_size_bytes is not None and len(data) > max_size_bytes:
        raise ValueError(
            f"El archivo excede el tamaño máximo permitido ({max_size_bytes // (1024 * 1024)} MB)."
        )

    folder = Path(settings.UPLOADS_DIR) / subfolder
    folder.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{ext}"
    destination = folder / filename
    destination.write_bytes(data)

    return f"/uploads/{subfolder}/{filename}", content_type


def save_bytes(data: bytes, *, subfolder: str, filename: str) -> str:
    """Persists raw bytes (not a client upload) under UPLOADS_DIR/<subfolder>/<filename>
    and returns the relative `/uploads/...` URL. Used to cache third-party media
    (e.g. a platform exercise's GIF) locally after fetching it once, instead of
    re-fetching from the vendor on every view."""
    folder = Path(settings.UPLOADS_DIR) / subfolder
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / filename
    destination.write_bytes(data)
    return f"/uploads/{subfolder}/{filename}"
