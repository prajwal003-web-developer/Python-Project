from datetime import datetime
from typing import Any

from pydantic import ConfigDict

from app.models.user import UserRole
from app.schemas.common import CamelModel
from app.schemas.user import UserAccount


class RoleUpdate(CamelModel):
    model_config = ConfigDict(extra="forbid")
    role: UserRole


class StatusUpdate(CamelModel):
    model_config = ConfigDict(extra="forbid")
    is_active: bool


class AdminUserOut(UserAccount):
    note_count: int = 0


def admin_user_out(doc: dict[str, Any], note_count: int = 0) -> AdminUserOut:
    return AdminUserOut(
        id=str(doc["_id"]), name=doc["name"], username=doc["username"], email=doc["email"],
        role=UserRole(doc["role"]), is_active=doc.get("isActive", True), note_count=note_count,
        created_at=doc["createdAt"], updated_at=doc["updatedAt"],
    )


class AuditLogOut(CamelModel):
    id: str
    action: str
    actor_id: str
    actor_username: str | None
    target_type: str
    target_id: str | None
    metadata: dict[str, Any]
    created_at: datetime


class DashboardCounts(CamelModel):
    users: int
    uploaders: int
    admins: int
    notes: int
    published_notes: int
    faculties: int
    departments: int
    pending_department_requests: int


class DashboardOut(CamelModel):
    counts: DashboardCounts
    recent_activity: list[AuditLogOut]
