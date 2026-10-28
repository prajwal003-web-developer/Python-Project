import re
from bson import ObjectId
from fastapi import HTTPException
from pymongo.errors import PyMongoError

from app.db.mongodb import db


async def get_notes_by_programme_and_semester(
    programme_id: str,
    semester: str,
):
    if not ObjectId.is_valid(programme_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid programme ID",
        )

    cursor = db["notes"].find({
        "programme": programme_id,
        "semester": semester,
    })

    notes = await cursor.to_list(length=None)
    formatted_notes = []

    for note in notes:
        note_id = str(note.pop("_id"))
        file_id = note.get("file_id")

        # Fetch the actual file metadata using file_id.
        file_doc = None

        if isinstance(file_id, str) and ObjectId.is_valid(file_id):
            file_doc = await db["files"].find_one(
                {"_id": ObjectId(file_id)},
                {
                    "secure_url": 1,
                    "original_filename": 1,
                    "size": 1,
                    "format": 1,
                },
            )

        note["id"] = note_id
        note["file_id"] = file_id
        note["file"] = None

        if file_doc:
            note["file"] = {
                "url": file_doc.get("secure_url"),
                "filename": file_doc.get("original_filename"),
                "size": file_doc.get("size"),
                "format": file_doc.get("format"),
            }

        note["uploader_id"] = str(note.get("uploader_id", ""))

        formatted_notes.append(note)

    return {
        "total": len(formatted_notes),
        "notes": formatted_notes,
    }

async def save_note(note_id: str, current_user: dict):
    if not ObjectId.is_valid(note_id):
        raise HTTPException(status_code=400, detail="Invalid note ID")

    note = await db["notes"].find_one({"_id": ObjectId(note_id)})

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    try:
        result = await db["users"].update_one(
            {"_id": current_user["_id"]},
            {"$addToSet": {"saved_notes": note_id}},
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")

        return {"message": "Note saved successfully"}

    except PyMongoError as exc:
        raise HTTPException(
            status_code=500, detail="Could not save note"
        ) from exc


async def unsave_note(note_id: str, current_user: dict):
    if not ObjectId.is_valid(note_id):
        raise HTTPException(status_code=400, detail="Invalid note ID")

    try:
        result = await db["users"].update_one(
            {"_id": current_user["_id"]},
            {"$pull": {"saved_notes": note_id}},
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")

        return {"message": "Note removed from saved notes"}

    except PyMongoError as exc:
        raise HTTPException(
            status_code=500, detail="Could not unsave note"
        ) from exc


async def get_saved_notes(current_user: dict):
    user = await db["users"].find_one(
        {"_id": current_user["_id"]},
        {"saved_notes": 1},
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    saved_ids = user.get("saved_notes", [])

    valid_ids = [
        ObjectId(note_id)
        for note_id in saved_ids
        if isinstance(note_id, str) and ObjectId.is_valid(note_id)
    ]

    if not valid_ids:
        return {"total": 0, "notes": []}

    cursor = db["notes"].find({"_id": {"$in": valid_ids}})
    notes = await cursor.to_list(length=None)

    # Keep notes in the same order as the user's saved list.
    notes_by_id = {str(note["_id"]): note for note in notes}
    ordered_notes = []

    for note_id in saved_ids:
        note = notes_by_id.get(note_id)

        if not note:
            continue

        note["id"] = str(note.pop("_id"))

        file_id = note.get("file_id")
        if isinstance(file_id, str) and ObjectId.is_valid(file_id):
            file_doc = await db["files"].find_one(
                {"_id": ObjectId(file_id)},
                {
                    "secure_url": 1,
                    "original_filename": 1,
                    "size": 1,
                    "format": 1,
                },
            )

            if file_doc:
                note["file"] = {
                    "url": file_doc.get("secure_url"),
                    "filename": file_doc.get("original_filename"),
                    "size": file_doc.get("size"),
                    "format": file_doc.get("format"),
                }

        note["file_id"] = file_id
        note["uploader_id"] = str(note["uploader_id"])
        ordered_notes.append(note)

    return {
        "total": len(ordered_notes),
        "notes": ordered_notes,
    }




async def find_by_id(collection_name: str, value):
    """Find a document using an ObjectId or a string ID."""
    if value is None:
        return None

    if isinstance(value, ObjectId):
        return await db[collection_name].find_one({"_id": value})

    value = str(value)

    if ObjectId.is_valid(value):
        document = await db[collection_name].find_one(
            {"_id": ObjectId(value)}
        )
        if document:
            return document

    return await db[collection_name].find_one({"_id": value})


async def search_notes(search: str):
    search = search.strip()

    if not search:
        return {"total": 0, "notes": []}

    pattern = re.escape(search)

    # Search note title, description and subject
    cursor = db["notes"].find({
        "$or": [
            {"title": {"$regex": pattern, "$options": "i"}},
            {"description": {"$regex": pattern, "$options": "i"}},
            {"subject": {"$regex": pattern, "$options": "i"}},
        ]
    }).limit(100)

    notes = await cursor.to_list(length=100)
    results = []

    for note in notes:
        # Fetch uploaded file
        file_doc = await find_by_id("files", note.get("file_id"))

        filename = (
            file_doc.get("original_filename", "")
            if file_doc
            else ""
        )

        # Match the uploaded filename too
        metadata_match = any(
            re.search(
                pattern,
                str(note.get(field, "")),
                re.IGNORECASE,
            )
            for field in ("title", "description", "subject")
        )

        filename_match = bool(
            filename and re.search(pattern, filename, re.IGNORECASE)
        )

        if not metadata_match and not filename_match:
            continue

        # Fetch programme
        programme_doc = await find_by_id(
            "programmes",
            note.get("programme"),
        )

        # Fetch faculty from the programme
        faculty_doc = None

        if programme_doc:
            # Support common faculty reference field names
            faculty_ref = (
                programme_doc.get("faculty")
                or programme_doc.get("faculty_id")
                or programme_doc.get("facultyId")
            )

            faculty_doc = await find_by_id(
                "faculties",
                faculty_ref,
            )

        # Replace the note ObjectId with a JSON-safe string
        note_id = str(note.pop("_id"))

        note["id"] = note_id
        note["file_id"] = (
            str(note["file_id"])
            if note.get("file_id") is not None
            else None
        )
        note["uploader_id"] = (
            str(note["uploader_id"])
            if note.get("uploader_id") is not None
            else None
        )

        # File details
        note["file"] = (
            {
                "url": file_doc.get("secure_url"),
                "filename": filename,
                "size": file_doc.get("size"),
                "format": file_doc.get("format"),
            }
            if file_doc
            else None
        )

        # Programme details
        note["programme_details"] = (
            {
                "id": str(programme_doc["_id"]),
                "name": programme_doc.get("name"),
                "slug": programme_doc.get("slug"),
            }
            if programme_doc
            else None
        )

        # Faculty details
        note["faculty_details"] = (
            {
                "id": str(faculty_doc["_id"]),
                "name": faculty_doc.get("name"),
                "slug": faculty_doc.get("slug"),
            }
            if faculty_doc
            else None
        )

        # Convert any remaining top-level ObjectIds to strings
        for key, value in note.items():
            if isinstance(value, ObjectId):
                note[key] = str(value)

        results.append(note)

    return {
        "total": len(results),
        "notes": results,
    }