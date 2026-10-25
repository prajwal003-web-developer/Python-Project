from typing import Any

from app.models.user import UserRole

User = dict[str, Any]


def is_admin(user: User) -> bool:
    return user.get("role") == UserRole.ADMIN


def can_upload_notes(user: User) -> bool:
    """Only the `uploader` role uploads (admins moderate; they are not uploaders)."""
    return user.get("role") == UserRole.UPLOADER


def is_owner(user: User, note: dict[str, Any]) -> bool:
    return note.get("uploadedBy") == user["_id"]


def can_manage_note(user: User, note: dict[str, Any]) -> bool:
    return is_owner(user, note) or is_admin(user)
