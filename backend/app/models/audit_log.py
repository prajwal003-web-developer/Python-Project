from datetime import datetime
from typing import Any

from bson import ObjectId


class AuditAction:
    FACULTY_CREATE = "faculty.create"
    FACULTY_UPDATE = "faculty.update"
    FACULTY_DELETE = "faculty.delete"
    DEPARTMENT_CREATE = "department.create"
    DEPARTMENT_UPDATE = "department.update"
    DEPARTMENT_DELETE = "department.delete"
    REQUEST_APPROVE = "department_request.approve"
    REQUEST_REJECT = "department_request.reject"
    NOTE_MODERATE = "note.moderate"
    NOTE_DELETE_BY_ADMIN = "note.delete_by_admin"
    USER_ROLE_CHANGE = "user.role_change"
    USER_STATUS_CHANGE = "user.status_change"


def build_audit_document(
    *, actor_id: ObjectId, action: str, target_type: str, target_id: ObjectId | None,
    metadata: dict[str, Any] | None, now: datetime,
) -> dict[str, Any]:
    """Metadata must be small and safe: never passwords, tokens or file contents."""
    return {"actorId": actor_id, "action": action, "targetType": target_type,
            "targetId": target_id, "metadata": metadata or {}, "createdAt": now}
