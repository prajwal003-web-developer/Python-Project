from datetime import datetime
from enum import StrEnum
from typing import Any


class UserRole(StrEnum):
    USER = "user"
    UPLOADER = "uploader"
    ADMIN = "admin"


def build_user_document(
    *, name: str, username: str, email: str, normalized_email: str,
    normalized_username: str, password_hash: str, now: datetime,
    role: UserRole = UserRole.USER,
) -> dict[str, Any]:
    """Shape of a document in the `users` collection."""
    return {
        "name": name,
        "username": username,
        "normalizedUsername": normalized_username,
        "email": email,
        "normalizedEmail": normalized_email,
        "passwordHash": password_hash,
        "role": role.value,
        "isActive": True,
        "createdAt": now,
        "updatedAt": now,
    }
