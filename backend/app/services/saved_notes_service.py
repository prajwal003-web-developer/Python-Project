from typing import Any

from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from app.core.exceptions import NotFoundError
from app.db.mongodb import Collections as C
from app.models.saved_note import build_saved_note_document
from app.schemas.common import PaginationParams, build_page
from app.schemas.note import SavedNoteOut
from app.services.notes_service import hydrate_notes
from app.utils.serialization import parse_object_id, utcnow

Doc = dict[str, Any]


async def save_note(db: AsyncDatabase, user: Doc, note_id: str) -> tuple[ObjectId, bool]:
    """Returns (note_id, created). Saving twice is a harmless no-op (unique index + upsert)."""
    oid = parse_object_id(note_id, "note id")
    if not await db[C.NOTES].find_one({"_id": oid, "isPublished": True}, projection={"_id": 1}):
        raise NotFoundError("note_not_found", "Note not found")
    try:
        result = await db[C.SAVED_NOTES].update_one(
            {"userId": user["_id"], "noteId": oid},
            {"$setOnInsert": build_saved_note_document(user_id=user["_id"], note_id=oid, now=utcnow())},
            upsert=True,
        )
    except DuplicateKeyError:  # two concurrent saves: the other one won
        return oid, False
    return oid, result.upserted_id is not None


async def unsave_note(db: AsyncDatabase, user: Doc, note_id: str) -> ObjectId:
    """Idempotent. Works even when the note no longer exists, so stale entries can always be cleared."""
    oid = parse_object_id(note_id, "note id")
    await db[C.SAVED_NOTES].delete_one({"userId": user["_id"], "noteId": oid})
    return oid


async def list_saved(db: AsyncDatabase, user: Doc, page: PaginationParams) -> dict[str, Any]:
    """Only the caller's own saves; entries whose note was deleted or unpublished are skipped."""
    base: list[Doc] = [
        {"$match": {"userId": user["_id"]}},
        {"$lookup": {"from": C.NOTES, "localField": "noteId", "foreignField": "_id", "as": "note"}},
        {"$unwind": "$note"},
        {"$match": {"note.isPublished": True}},
    ]
    saved = db[C.SAVED_NOTES]
    count_cursor = await saved.aggregate([*base, {"$count": "n"}])
    counted = await count_cursor.to_list(1)
    total = counted[0]["n"] if counted else 0
    cursor = await saved.aggregate([*base, {"$sort": {"createdAt": -1, "_id": -1}},
                                    {"$skip": page.skip}, {"$limit": page.limit}])
    rows = await cursor.to_list(None)
    notes = await hydrate_notes(db, [r["note"] for r in rows])
    items = [SavedNoteOut(saved_at=r["createdAt"], note=n) for r, n in zip(rows, notes)]
    return build_page(items, total, page.page, page.limit)
