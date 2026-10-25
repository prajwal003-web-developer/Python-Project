from datetime import datetime
from typing import Any


def build_faculty_document(*, name: str, slug: str, description: str, now: datetime) -> dict[str, Any]:
    return {"name": name, "slug": slug, "description": description, "isActive": True,
            "createdAt": now, "updatedAt": now}
