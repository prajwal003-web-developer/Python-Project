import re
from typing import Any

from bson import ObjectId
from fastapi import UploadFile
from pymongo import ASCENDING, DESCENDING, ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, NotFoundError, UnprocessableError
from app.core.permissions import can_upload_notes, is_admin, is_owner
from app.db.mongodb import Collections as C
from app.models.audit_log import AuditAction
from app.models.note import build_note_document
from app.schemas.common import PaginationParams, build_page
from app.schemas.note import NoteCreate, NoteOut, NoteUpdate, UploadStats, note_out
from app.services import cloudinary_service
from app.services.audit_service import record_audit
from app.utils.file_validation import validate_upload
from app.utils.serialization import parse_object_id, utcnow

Doc = dict[str, Any]
SORT_FIELDS = {"createdAt", "updatedAt", "title"}  # explicit allow-list


# ---------------- shared helpers (also used by public browsing / saved notes) ----------------
async def hydrate_notes(db: AsyncDatabase, docs: list[Doc]) -> list[NoteOut]:
    """Attach uploader/faculty/department names with three batched queries."""
    if not docs:
        return []
    users = await db[C.USERS].find({"_id": {"$in": list({d["uploadedBy"] for d in docs})}},
                                   projection={"name": 1, "username": 1}).to_list(None)
    faculties = await db[C.FACULTIES].find({"_id": {"$in": list({d["facultyId"] for d in docs})}},
                                           projection={"name": 1}).to_list(None)
    depts = await db[C.DEPARTMENTS].find({"_id": {"$in": list({d["departmentId"] for d in docs})}},
                                         projection={"name": 1}).to_list(None)
    u, f, d = ({x["_id"]: x for x in rows} for rows in (users, faculties, depts))
    return [note_out(n, u.get(n["uploadedBy"]), f.get(n["facultyId"]), d.get(n["departmentId"])) for n in docs]


async def hydrate_note(db: AsyncDatabase, doc: Doc) -> NoteOut:
    return (await hydrate_notes(db, [doc]))[0]


async def get_note_or_404(db: AsyncDatabase, note_id: str) -> Doc:
    note = await db[C.NOTES].find_one({"_id": parse_object_id(note_id, "note id")})
    if not note:
        raise NotFoundError("note_not_found", "Note not found")
    return note


def _deny(note: Doc) -> Exception:
    """Do not reveal that an unpublished note exists to people who may not see it."""
    if note.get("isPublished", True):
        return ForbiddenError("not_note_owner", "You do not have permission to modify this note")
    return NotFoundError("note_not_found", "Note not found")


async def _validate_target(db: AsyncDatabase, faculty_id: ObjectId, department_id: ObjectId, semester: int) -> None:
    if not 1 <= semester <= get_settings().max_semesters:
        raise UnprocessableError("invalid_semester", f"Semester must be between 1 and {get_settings().max_semesters}")
    if not await db[C.FACULTIES].find_one({"_id": faculty_id, "isActive": True}, projection={"_id": 1}):
        raise NotFoundError("faculty_not_found", "Faculty not found")
    if not await db[C.DEPARTMENTS].find_one(
        {"_id": department_id, "facultyId": faculty_id, "isActive": True}, projection={"_id": 1}
    ):
        raise NotFoundError("department_not_found", "Department not found in the selected faculty")


# ---------------- create ----------------
async def create_note(db: AsyncDatabase, user: Doc, data: NoteCreate, upload: UploadFile | None) -> Doc:
    faculty_id = parse_object_id(data.faculty_id, "faculty id")
    department_id = parse_object_id(data.department_id, "department id")
    await _validate_target(db, faculty_id, department_id, data.semester)   # 2. validate target
    file = await validate_upload(upload)                                    # 3. validate file
    asset = await cloudinary_service.upload_note_file(file)                 # 4. upload
    doc = build_note_document(
        title=data.title, description=data.description, subject=data.subject, faculty_id=faculty_id,
        department_id=department_id, semester=data.semester, file_type=file.file_type, file_url=asset.url,
        public_id=asset.public_id, file_size=asset.size, uploaded_by=user["_id"], now=utcnow(),
    )
    try:
        await db[C.NOTES].insert_one(doc)                                   # 5. save metadata
    except Exception:
        await cloudinary_service.safe_delete_asset(asset.public_id)         # 6. compensate
        raise
    return doc


# ---------------- update / moderate ----------------
async def update_note(db: AsyncDatabase, actor: Doc, note_id: str, data: NoteUpdate) -> Doc:
    note = await get_note_or_404(db, note_id)
    changes = data.model_dump(exclude_unset=True)
    updates: Doc = {}
    owner, moderation = is_owner(actor, note), False

    if owner and can_upload_notes(actor):
        for key in ("title", "description", "subject", "semester"):
            if key in changes:
                updates[key] = changes[key]
        if {"faculty_id", "department_id", "semester"} & changes.keys():
            fid = parse_object_id(changes["faculty_id"], "faculty id") if changes.get("faculty_id") else note["facultyId"]
            did = parse_object_id(changes["department_id"], "department id") if changes.get("department_id") else note["departmentId"]
            await _validate_target(db, fid, did, changes.get("semester", note["semester"]))
            updates["facultyId"], updates["departmentId"] = fid, did
        if "is_published" in changes:
            if changes["is_published"] and note.get("hiddenByAdmin"):
                raise ForbiddenError("hidden_by_admin", "This note was hidden by a moderator")
            updates["isPublished"] = changes["is_published"]
    elif is_admin(actor):
        moderation = True
        if set(changes) - {"is_published"}:
            raise ForbiddenError("moderation_only", "Administrators may only publish or unpublish notes")
        if "is_published" in changes:
            updates["isPublished"] = changes["is_published"]
            updates["hiddenByAdmin"] = not changes["is_published"]
    elif owner:
        raise ForbiddenError("uploader_required", "Uploader permission is required to edit notes")
    else:
        raise _deny(note)

    if not updates:
        return note
    updates["updatedAt"] = utcnow()
    updated = await db[C.NOTES].find_one_and_update({"_id": note["_id"]}, {"$set": updates},
                                                    return_document=ReturnDocument.AFTER)
    if updated is None:
        raise NotFoundError("note_not_found", "Note not found")
    if moderation:
        await record_audit(db, actor, AuditAction.NOTE_MODERATE, "note", note["_id"],
                           {"isPublished": updates.get("isPublished"), "title": note["title"]})
    return updated


# ---------------- replace file ----------------
async def replace_file(db: AsyncDatabase, actor: Doc, note_id: str, upload: UploadFile | None) -> Doc:
    note = await get_note_or_404(db, note_id)
    if not is_owner(actor, note):
        raise _deny(note)
    if not can_upload_notes(actor):
        raise ForbiddenError("uploader_required", "Uploader permission is required to replace files")

    file = await validate_upload(upload)
    asset = await cloudinary_service.upload_note_file(file)     # old file is untouched until DB succeeds
    try:
        updated = await db[C.NOTES].find_one_and_update(
            {"_id": note["_id"], "uploadedBy": actor["_id"]},
            {"$set": {"fileUrl": asset.url, "publicId": asset.public_id, "fileType": file.file_type,
                      "fileSize": asset.size, "updatedAt": utcnow()}},
            return_document=ReturnDocument.AFTER,
        )
    except Exception:
        await cloudinary_service.safe_delete_asset(asset.public_id)
        raise
    if updated is None:  # note vanished mid-flight
        await cloudinary_service.safe_delete_asset(asset.public_id)
        raise NotFoundError("note_not_found", "Note not found")
    await cloudinary_service.safe_delete_asset(note["publicId"])  # only now remove the previous asset
    return updated


# ---------------- delete ----------------
async def delete_note(db: AsyncDatabase, actor: Doc, note_id: str) -> None:
    note = await get_note_or_404(db, note_id)
    owner = is_owner(actor, note)
    if not owner and not is_admin(actor):
        raise _deny(note)

    result = await db[C.NOTES].delete_one({"_id": note["_id"]})
    if result.deleted_count == 0:
        raise NotFoundError("note_not_found", "Note not found")
    await db[C.SAVED_NOTES].delete_many({"noteId": note["_id"]})
    await cloudinary_service.safe_delete_asset(note["publicId"])  # DB first: a failure never leaves a dead link
    if not owner:
        await record_audit(db, actor, AuditAction.NOTE_DELETE_BY_ADMIN, "note", note["_id"],
                           {"title": note["title"], "uploadedBy": str(note["uploadedBy"])})


# ---------------- uploader dashboard ----------------
async def my_notes(
    db: AsyncDatabase, user: Doc, page: PaginationParams, *, q: str | None, file_type: str | None,
    sort_by: str, sort_order: str,
) -> dict[str, Any]:
    if sort_by not in SORT_FIELDS:
        raise UnprocessableError("invalid_sort", f"sortBy must be one of {sorted(SORT_FIELDS)}")
    query: Doc = {"uploadedBy": user["_id"]}
    if file_type:
        query["fileType"] = file_type
    if q:
        rx = {"$regex": re.escape(q), "$options": "i"}  # escaped: user input is never a regex/operator
        query["$or"] = [{"title": rx}, {"description": rx}, {"subject": rx}]

    notes = db[C.NOTES]
    total = await notes.count_documents(query)
    direction = ASCENDING if sort_order == "asc" else DESCENDING
    docs = await notes.find(query).sort([(sort_by, direction), ("_id", direction)]) \
        .skip(page.skip).limit(page.limit).to_list(None)

    cursor = await notes.aggregate([
        {"$match": {"uploadedBy": user["_id"]}},
        {"$group": {
            "_id": None, "total": {"$sum": 1},
            "published": {"$sum": {"$cond": ["$isPublished", 1, 0]}},
            "pdf": {"$sum": {"$cond": [{"$eq": ["$fileType", "pdf"]}, 1, 0]}},
            "docx": {"$sum": {"$cond": [{"$eq": ["$fileType", "docx"]}, 1, 0]}},
            "size": {"$sum": "$fileSize"}, "first": {"$min": "$createdAt"}, "last": {"$max": "$createdAt"},
        }},
    ])
    agg = await cursor.to_list(1)
    g = agg[0] if agg else {}
    stats = UploadStats(
        total_notes=g.get("total", 0), published_notes=g.get("published", 0),
        unpublished_notes=g.get("total", 0) - g.get("published", 0), pdf_count=g.get("pdf", 0),
        docx_count=g.get("docx", 0), total_file_size=g.get("size", 0),
        first_uploaded_at=g.get("first"), last_uploaded_at=g.get("last"),
    )
    items = await hydrate_notes(db, docs)
    return {"stats": stats, "notes": build_page(items, total, page.page, page.limit)}


# ---------------- public browsing (Phase 5) ----------------
def _sort_spec(sort_by: str, sort_order: str) -> list[tuple[str, int]]:
    if sort_by not in SORT_FIELDS:
        raise UnprocessableError("invalid_sort", f"sortBy must be one of {sorted(SORT_FIELDS)}")
    direction = ASCENDING if sort_order == "asc" else DESCENDING
    return [(sort_by, direction), ("_id", direction)]  # _id tie-break keeps pagination stable


async def search_public_notes(
    db: AsyncDatabase, page: PaginationParams, *, q: str | None = None, faculty_id: str | None = None,
    department_id: str | None = None, semester: int | None = None, username: str | None = None,
    file_type: str | None = None, sort_by: str = "createdAt", sort_order: str = "desc",
    uploaded_by: ObjectId | None = None,
) -> dict[str, Any]:
    """Published notes only. Every value is typed/escaped; no client value is ever used as an operator."""
    sort = _sort_spec(sort_by, sort_order)
    query: Doc = {"isPublished": True}
    if uploaded_by is not None:
        query["uploadedBy"] = uploaded_by
    if username:
        user = await db[C.USERS].find_one({"normalizedUsername": username.strip().lower()}, projection={"_id": 1})
        if not user:
            return build_page([], 0, page.page, page.limit)
        query["uploadedBy"] = user["_id"]
    if faculty_id:
        query["facultyId"] = parse_object_id(faculty_id, "faculty id")
    if department_id:
        query["departmentId"] = parse_object_id(department_id, "department id")
    if semester is not None:
        query["semester"] = semester
    if file_type:
        query["fileType"] = file_type
    if q:
        rx = {"$regex": re.escape(q.strip()), "$options": "i"}
        query["$or"] = [{"title": rx}, {"description": rx}, {"subject": rx}]

    notes = db[C.NOTES]
    total = await notes.count_documents(query)
    docs = await notes.find(query).sort(sort).skip(page.skip).limit(page.limit).to_list(None)
    return build_page(await hydrate_notes(db, docs), total, page.page, page.limit)


async def get_visible_note(db: AsyncDatabase, note_id: str, viewer: Doc | None) -> Doc:
    """Published notes are public; unpublished ones are visible only to their owner and admins."""
    note = await get_note_or_404(db, note_id)
    if note.get("isPublished", True):
        return note
    if viewer is not None and (is_owner(viewer, note) or is_admin(viewer)):
        return note
    raise NotFoundError("note_not_found", "Note not found")
