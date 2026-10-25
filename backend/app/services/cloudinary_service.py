import asyncio
import io
import logging
import uuid
from dataclasses import dataclass

import cloudinary
import cloudinary.uploader

from app.core.config import get_settings
from app.core.exceptions import UpstreamError
from app.utils.file_validation import ValidatedFile

logger = logging.getLogger("app.cloudinary")


@dataclass(frozen=True)
class UploadedAsset:
    url: str
    public_id: str
    size: int


def _configure() -> None:
    s = get_settings()
    secret = s.cloudinary_api_secret.get_secret_value()
    if not (s.cloudinary_cloud_name and s.cloudinary_api_key and secret):
        raise UpstreamError("storage_not_configured", "File storage is not configured")
    cloudinary.config(cloud_name=s.cloudinary_cloud_name, api_key=s.cloudinary_api_key,
                      api_secret=secret, secure=True)


def _upload_sync(file: ValidatedFile) -> UploadedAsset:
    _configure()
    folder = get_settings().cloudinary_folder.strip("/")
    # "raw" delivery keeps PDF and DOCX byte-for-byte; raw public IDs must carry the extension.
    public_id = f"{folder}/{uuid.uuid4().hex}-{file.safe_stem}.{file.file_type}"
    result = cloudinary.uploader.upload(
        io.BytesIO(file.content), resource_type="raw", type="upload", public_id=public_id,
        overwrite=False, unique_filename=False, use_filename=False,
    )
    return UploadedAsset(url=result["secure_url"], public_id=result["public_id"],
                         size=int(result.get("bytes", file.size)))


def _delete_sync(public_id: str) -> None:
    _configure()
    result = cloudinary.uploader.destroy(public_id, resource_type="raw", type="upload", invalidate=True)
    if result.get("result") not in ("ok", "not found"):
        raise UpstreamError("delete_failed", "Failed to delete file from storage")


async def upload_note_file(file: ValidatedFile) -> UploadedAsset:
    try:
        return await asyncio.to_thread(_upload_sync, file)
    except UpstreamError:
        raise
    except Exception as exc:  # Cloudinary SDK errors; never leak details to the client
        logger.error("Cloudinary upload failed: %s", type(exc).__name__)
        raise UpstreamError("upload_failed", "Failed to upload file to storage") from exc


async def delete_asset(public_id: str) -> None:
    try:
        await asyncio.to_thread(_delete_sync, public_id)
    except UpstreamError:
        raise
    except Exception as exc:
        logger.error("Cloudinary delete failed: %s", type(exc).__name__)
        raise UpstreamError("delete_failed", "Failed to delete file from storage") from exc


async def safe_delete_asset(public_id: str) -> None:
    """Compensation helper: never raises; logs the orphan so it can be cleaned up manually."""
    try:
        await delete_asset(public_id)
    except Exception:
        logger.error("ORPHANED Cloudinary asset needs manual cleanup: %s", public_id)
