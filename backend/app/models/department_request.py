from datetime import datetime
from enum import StrEnum
from typing import Any

from bson import ObjectId


class RequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


def build_request_document(
    *, name: str, slug: str, faculty_id: ObjectId, description: str, requested_by: ObjectId, now: datetime
) -> dict[str, Any]:
    return {
        "name": name, "slug": slug, "facultyId": faculty_id, "description": description,
        "requestedBy": requested_by, "status": RequestStatus.PENDING.value,
        "adminComment": None, "reviewedBy": None, "reviewedAt": None, "departmentId": None,
        "createdAt": now, "updatedAt": now,
    }
