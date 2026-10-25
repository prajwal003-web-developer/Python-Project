import re
import unicodedata

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_line(value: str, min_len: int, max_len: int, label: str) -> str:
    """Single-line text: strips control characters and collapses whitespace."""
    value = " ".join(_CONTROL.sub("", value).split())
    if not min_len <= len(value) <= max_len:
        raise ValueError(f"{label} must be between {min_len} and {max_len} characters")
    return value


def clean_block(value: str, max_len: int, label: str) -> str:
    """Multi-line text (descriptions). Keeps newlines, strips control characters."""
    value = _CONTROL.sub("", value.replace("\r\n", "\n").replace("\r", "\n")).strip()
    if len(value) > max_len:
        raise ValueError(f"{label} must be at most {max_len} characters")
    return value


def slugify(value: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")[:80].strip("-")
    if not slug:
        raise ValueError("Name must contain at least one letter or digit")
    return slug
