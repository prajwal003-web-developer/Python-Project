from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId

from app.core.exceptions import BadRequestError


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def parse_object_id(value: str, field: str = "id") -> ObjectId:
    """Strict 24-hex ObjectId parsing; invalid values -> 400 (never reaches the database)."""
    if not isinstance(value, str) or len(value) != 24:
        raise BadRequestError("invalid_id", f"Invalid {field}")
    try:
        return ObjectId(value)
    except (InvalidId, TypeError) as exc:
        raise BadRequestError("invalid_id", f"Invalid {field}") from exc
