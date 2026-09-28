"""Article cover photos, stored in the database so a restart cannot drop them."""

import re
import uuid

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.models.article import ArticleImage

MAX_IMAGE_BYTES = 5 * 1024 * 1024
_NAME = re.compile(r"^[a-f0-9]{32}\.(jpg|png|gif|webp)$")
_PREFIX = "/media/articles/"

_SIGNATURES: tuple[tuple[bytes, str, str], ...] = (
    (b"\xff\xd8\xff", "image/jpeg", "jpg"),
    (b"\x89PNG\r\n\x1a\n", "image/png", "png"),
    (b"GIF87a", "image/gif", "gif"),
    (b"GIF89a", "image/gif", "gif"),
    (b"RIFF", "image/webp", "webp"),
)


def _kind(payload: bytes) -> tuple[str, str] | None:
    for magic, content_type, ext in _SIGNATURES:
        if not payload.startswith(magic):
            continue
        if ext == "webp" and payload[8:12] != b"WEBP":
            continue
        return content_type, ext
    return None


def image_name(public_path: str | None) -> str | None:
    if not public_path or not public_path.startswith(_PREFIX):
        return None
    name = public_path.removeprefix(_PREFIX)
    return name if _NAME.fullmatch(name) else None


async def save_article_image(db: AsyncSession, upload: UploadFile) -> str:
    payload = await upload.read(MAX_IMAGE_BYTES + 1)
    kind = _kind(payload)
    if kind is None or len(payload) > MAX_IMAGE_BYTES:
        raise AppError(
            "Upload a JPG, PNG, GIF, or WebP image up to 5 MB",
            status_code=422,
            code="invalid_image",
        )
    content_type, ext = kind
    name = f"{uuid.uuid4().hex}.{ext}"
    db.add(ArticleImage(name=name, content_type=content_type, data=payload))
    await db.flush()
    return f"{_PREFIX}{name}"


async def delete_article_image(db: AsyncSession, public_path: str | None) -> None:
    name = image_name(public_path)
    if name is None:
        return
    row = await db.get(ArticleImage, name)
    if row is not None:
        await db.delete(row)


async def load_article_image(db: AsyncSession, filename: str) -> tuple[bytes, str] | None:
    if not _NAME.fullmatch(filename):
        return None
    row = await db.get(ArticleImage, filename)
    if row is not None:
        return bytes(row.data), row.content_type
    path = (settings.media_root / "articles" / filename).resolve()
    root = (settings.media_root / "articles").resolve()
    if path.parent != root or not path.is_file():
        return None
    content_type = {
        ".jpg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(path.suffix, "application/octet-stream")
    return path.read_bytes(), content_type
