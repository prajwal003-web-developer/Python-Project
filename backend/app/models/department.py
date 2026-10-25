from datetime import datetime
from typing import Any

from bson import ObjectId


def build_department_document(
    *, name: str, slug: str, faculty_id: ObjectId, description: str, now: datetime
) -> dict[str, Any]:
    return {"name": name, "slug": slug, "facultyId": faculty_id, "description": description,
            "isActive": True, "createdAt": now, "updatedAt": now}
