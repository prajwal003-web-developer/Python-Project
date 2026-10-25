from datetime import datetime
from typing import Any

from bson import ObjectId


def build_saved_note_document(*, user_id: ObjectId, note_id: ObjectId, now: datetime) -> dict[str, Any]:
    return {"userId": user_id, "noteId": note_id, "createdAt": now}
