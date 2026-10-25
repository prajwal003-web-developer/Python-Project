import io
import os
import re
import unicodedata
import zipfile
from dataclasses import dataclass

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import BadRequestError, PayloadTooLargeError, UnsupportedMediaTypeError

PDF_MIME = "application/pdf"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
ALLOWED = {".pdf": ("pdf", {PDF_MIME}), ".docx": ("docx", {DOCX_MIME})}
# Browsers/clients sometimes send these for valid files; the signature check is authoritative.
NEUTRAL_MIME = {"", "application/octet-stream"}

MAX_ZIP_ENTRIES = 5000
MAX_UNCOMPRESSED_BYTES = 200 * 1024 * 1024  # zip-bomb guard for DOCX


@dataclass(frozen=True)
class ValidatedFile:
    content: bytes
    file_type: str  # "pdf" | "docx"
    safe_stem: str
    size: int


def sanitize_filename(filename: str) -> tuple[str, str]:
    """Returns (safe_stem, lowercase_extension). Strips paths, unicode tricks and odd characters."""
    base = os.path.basename((filename or "").replace("\\", "/"))
    stem, ext = os.path.splitext(base)
    stem = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode()
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", stem).strip("._-")[:60] or "note"
    return stem, ext.lower()


async def read_limited(upload: UploadFile, max_bytes: int) -> bytes:
    """Reads at most max_bytes+1 so an oversized upload is never fully buffered."""
    data = await upload.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise PayloadTooLargeError(
            "file_too_large", f"File exceeds the maximum size of {get_settings().max_upload_size_mb} MB"
        )
    return data


def _check_docx(data: bytes) -> None:
    if not data.startswith(b"PK\x03\x04"):
        raise UnsupportedMediaTypeError("invalid_docx", "File content is not a valid DOCX document")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            infos = zf.infolist()
            names = {i.filename for i in infos}
            if len(infos) > MAX_ZIP_ENTRIES or sum(i.file_size for i in infos) > MAX_UNCOMPRESSED_BYTES:
                raise UnsupportedMediaTypeError("invalid_docx", "DOCX archive is too large or malformed")
            if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                raise UnsupportedMediaTypeError("invalid_docx", "File content is not a valid DOCX document")
    except zipfile.BadZipFile as exc:
        raise UnsupportedMediaTypeError("invalid_docx", "File content is not a valid DOCX document") from exc


async def validate_upload(upload: UploadFile | None) -> ValidatedFile:
    if upload is None or not upload.filename:
        raise BadRequestError("file_required", "A PDF or DOCX file is required")

    stem, ext = sanitize_filename(upload.filename)
    if ext not in ALLOWED:
        raise UnsupportedMediaTypeError("unsupported_file_type", "Only PDF and DOCX files are allowed")
    file_type, mimes = ALLOWED[ext]

    declared = (upload.content_type or "").split(";")[0].strip().lower()
    if declared not in mimes and declared not in NEUTRAL_MIME:
        raise UnsupportedMediaTypeError("mime_mismatch", "File type does not match its extension")

    data = await read_limited(upload, get_settings().max_upload_size_bytes)
    if not data:
        raise BadRequestError("empty_file", "The uploaded file is empty")

    if file_type == "pdf":
        if not data.startswith(b"%PDF-"):
            raise UnsupportedMediaTypeError("invalid_pdf", "File content is not a valid PDF")
    else:
        _check_docx(data)

    return ValidatedFile(content=data, file_type=file_type, safe_stem=stem, size=len(data))
