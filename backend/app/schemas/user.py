import re
from datetime import datetime
from typing import Any

from pydantic import ConfigDict, field_validator, model_validator

from app.core.security import validate_password_strength
from app.models.user import UserRole
from app.schemas.common import CamelModel

USERNAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.]{2,29}$")
RESERVED_USERNAMES = frozenset({
    "admin", "administrator", "root", "system", "support", "moderator", "api", "me",
    "null", "undefined", "anonymous", "uploader",
})


def clean_name(value: str) -> str:
    value = " ".join(value.split())
    if not 2 <= len(value) <= 100:
        raise ValueError("Name must be between 2 and 100 characters")
    return value


def clean_username(value: str) -> str:
    value = value.strip()
    if not USERNAME_RE.fullmatch(value) or ".." in value:
        raise ValueError(
            "Username must be 3-30 characters, start with a letter, and contain only "
            "letters, numbers, underscores or single dots"
        )
    if value.lower() in RESERVED_USERNAMES:
        raise ValueError("This username is reserved")
    return value


class UserAccount(CamelModel):
    """Returned only to the authenticated owner (and admins). Never includes passwordHash."""

    id: str
    name: str
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PublicUser(CamelModel):
    """Safe public fields only."""

    name: str
    username: str


class ProfileUpdate(CamelModel):
    """PATCH /auth/me. `extra=forbid` blocks mass assignment (role, isActive, email...)."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    username: str | None = None
    current_password: str | None = None
    new_password: str | None = None

    @field_validator("name")
    @classmethod
    def _name(cls, v: str | None) -> str | None:
        return None if v is None else clean_name(v)

    @field_validator("username")
    @classmethod
    def _username(cls, v: str | None) -> str | None:
        return None if v is None else clean_username(v)

    @field_validator("new_password")
    @classmethod
    def _new_password(cls, v: str | None) -> str | None:
        return None if v is None else validate_password_strength(v)

    @model_validator(mode="after")
    def _check(self) -> "ProfileUpdate":
        if bool(self.current_password) != bool(self.new_password):
            raise ValueError("currentPassword and newPassword must be provided together")
        if not any([self.name, self.username, self.new_password]):
            raise ValueError("No fields to update")
        return self


def user_account(doc: dict[str, Any]) -> UserAccount:
    return UserAccount(
        id=str(doc["_id"]), name=doc["name"], username=doc["username"], email=doc["email"],
        role=UserRole(doc["role"]), is_active=doc.get("isActive", True),
        created_at=doc["createdAt"], updated_at=doc["updatedAt"],
    )
