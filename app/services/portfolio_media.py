"""Store portfolio card images on disk and expose them under /media."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import UploadFile
from fastapi.exceptions import RequestValidationError

from app.core.config import settings

MAX_IMAGE_BYTES = 5 * 1024 * 1024
_SIGNATURES: tuple[tuple[bytes, str], ...] = (
    (b"\xff\xd8\xff", "jpg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"GIF87a", "gif"),
    (b"GIF89a", "gif"),
)


def portfolio_dir() -> Path:
    folder = Path(settings.media_root) / "portfolio"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _kind(header: bytes) -> str | None:
    for signature, extension in _SIGNATURES:
        if header.startswith(signature):
            return extension
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "webp"
    return None


def _reject(message: str) -> RequestValidationError:
    return RequestValidationError(
        [{"type": "value_error", "loc": ("image",), "msg": message, "input": None}]
    )


async def save_portfolio_image(upload: UploadFile) -> str:
    """Persist an uploaded card image. Returns the public path."""
    raw = await upload.read(MAX_IMAGE_BYTES + 1)
    await upload.close()
    if not raw:
        raise _reject("Add an image.")
    if len(raw) > MAX_IMAGE_BYTES:
        raise _reject("Use an image smaller than 5 MB.")
    extension = _kind(raw[:16])
    if extension is None:
        raise _reject("Use a JPG, PNG, WebP, or GIF image.")

    name = f"{uuid.uuid4().hex}.{extension}"
    destination = portfolio_dir() / name
    destination.write_bytes(raw)
    return f"/media/portfolio/{name}"


def delete_portfolio_image(public_path: str | None) -> None:
    if not public_path or not public_path.startswith("/media/portfolio/"):
        return
    name = Path(public_path).name
    if not name or name in {".", ".."}:
        return
    target = portfolio_dir() / name
    if target.is_file():
        target.unlink()
