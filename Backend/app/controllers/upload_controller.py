
import logging
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import cloudinary.uploader
from bson import ObjectId
from fastapi import HTTPException, UploadFile
from pymongo.errors import PyMongoError
from starlette.concurrency import run_in_threadpool

# IMPORTANT: Import this to load Cloudinary configuration.
from app.db.cloudinary import cloudinary_settings
from app.db.mongodb import db


logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".ppt", ".pptx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


async def upload_note_file(
    file: UploadFile,
    title: str,
    description: str,
    faculty: str,
    programme: str,
    semester: str,
    subject: str,
    current_user: dict,
):
    filename = Path(file.filename or "").name
    extension = Path(filename).suffix.lower()

    if not filename or extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOCX, PPT, and PPTX files are allowed.",
        )

    if not title.strip():
        raise HTTPException(status_code=400, detail="Title is required.")

    if not subject.strip():
        raise HTTPException(status_code=400, detail="Subject is required.")

    user_id = current_user.get("_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authenticated user ID is missing.",
        )

    file_bytes = await file.read()

    try:
        if not file_bytes:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty.",
            )

        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Maximum file size is 10 MB.",
            )

        cloudinary_result = None
        file_id = None

        try:
            # Upload the document to Cloudinary.
            cloudinary_result = await run_in_threadpool(
                cloudinary.uploader.upload,
                BytesIO(file_bytes),
                resource_type="raw",
                folder="adtu_notes",
                public_id=f"{uuid4().hex}{extension}",
                overwrite=False,
            )

            file_document = {
                "cloudinary_id": cloudinary_result["public_id"],
                "secure_url": cloudinary_result["secure_url"],
                "original_filename": filename,
                "size": len(file_bytes),
                "format": extension.lstrip("."),
                "uploader_id": str(user_id),
                "created_at": datetime.now(timezone.utc),
            }

            # Save file metadata in MongoDB.
            file_result = await db["files"].insert_one(file_document)
            file_id = file_result.inserted_id

            note_document = {
                "title": title.strip(),
                "description": description.strip(),
                "faculty": faculty,
                "programme": programme,
                "semester": semester,
                "subject": subject.strip(),
                "file_id": str(file_id),
                "uploader_id": str(user_id),
                "created_at": datetime.now(timezone.utc),
            }

            # Save note metadata in MongoDB.
            note_result = await db["notes"].insert_one(note_document)

            return {
                "message": "Note uploaded successfully.",
                "note": {
                    "id": str(note_result.inserted_id),
                    "title": note_document["title"],
                    "description": note_document["description"],
                    "faculty": faculty,
                    "programme": programme,
                    "semester": semester,
                    "subject": note_document["subject"],
                    "file_id": str(file_id),
                    "filename": filename,
                    "size": len(file_bytes),
                    "file_url": cloudinary_result["secure_url"],
                    "uploader_id": str(user_id),
                    "created_at": note_document["created_at"].isoformat(),
                },
            }

        except HTTPException:
            raise

        except Exception as exc:
            logger.exception("Note upload failed")

            # Remove a partially created database file record.
            if file_id is not None:
                try:
                    await db["files"].delete_one({"_id": file_id})
                except Exception:
                    logger.exception("Failed to remove file metadata")

            # Remove the uploaded Cloudinary file if possible.
            if cloudinary_result and cloudinary_result.get("public_id"):
                try:
                    await run_in_threadpool(
                        cloudinary.uploader.destroy,
                        cloudinary_result["public_id"],
                        resource_type="raw",
                    )
                except Exception:
                    logger.exception("Cloudinary cleanup failed")

            if isinstance(exc, PyMongoError):
                raise HTTPException(
                    status_code=500,
                    detail="Could not save note metadata in MongoDB.",
                ) from exc

            # Keep the detailed error in server logs, not the public response.
            raise HTTPException(
                status_code=502,
                detail="File upload or database operation failed. Check backend logs.",
            ) from exc

    finally:
        await file.close()




async def delete_note(note_id: str, current_user: dict):
    # Validate the note ID
    if not ObjectId.is_valid(note_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid note ID.",
        )

    user_id = current_user.get("_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authenticated user ID is missing.",
        )

    # Find the note
    note = await db["notes"].find_one(
        {"_id": ObjectId(note_id)}
    )

    if not note:
        raise HTTPException(
            status_code=404,
            detail="Note not found.",
        )

    # Only the original uploader can delete this note
    if str(note.get("uploader_id")) != str(user_id):
        raise HTTPException(
            status_code=403,
            detail="You can only delete notes you uploaded.",
        )

    file_id = note.get("file_id")
    file_doc = None

    # Find associated file metadata
    if file_id and ObjectId.is_valid(str(file_id)):
        file_doc = await db["files"].find_one(
            {"_id": ObjectId(str(file_id))}
        )

    # Check whether another note references the same file
    other_references = 0

    if file_id:
        other_references = await db["notes"].count_documents({
            "file_id": str(file_id),
            "_id": {"$ne": ObjectId(note_id)},
        })

    # Delete the note first
    try:
        await db["notes"].delete_one(
            {"_id": ObjectId(note_id)}
        )
    except Exception as exc:
        logger.exception("Failed to delete note from MongoDB")
        raise HTTPException(
            status_code=500,
            detail="Could not delete note.",
        ) from exc

    # Delete the file only if no other notes use it
    if file_doc and other_references == 0:
        cloudinary_id = file_doc.get("cloudinary_id")

        if cloudinary_id:
            try:
                result = await run_in_threadpool(
                    cloudinary.uploader.destroy,
                    cloudinary_id,
                    resource_type="raw",
                )

                if result.get("result") not in ("ok", "not found"):
                    logger.error(
                        "Cloudinary deletion returned: %s",
                        result.get("result"),
                    )
            except Exception:
                # The note is deleted, but the remote file may remain.
                logger.exception(
                    "Note deleted, but Cloudinary file cleanup failed"
                )

        # Remove file metadata from MongoDB
        try:
            await db["files"].delete_one(
                {"_id": file_doc["_id"]}
            )
        except Exception:
            logger.exception(
                "Note deleted, but file metadata cleanup failed"
            )

    return {
        "message": "Note deleted successfully.",
        "note_id": note_id,
    }
async def get_my_notes(current_user: dict):
    user_id = current_user.get("_id")

    print(user_id)

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authenticated user ID is missing.",
        )

    try:
        # Find only notes uploaded by the logged-in user.
        cursor = db["notes"].find(
            {"uploader_id": str(user_id)}
        ).sort("created_at", -1)

        notes = await cursor.to_list(length=None)

        # Collect valid file IDs so we can fetch file metadata together.
        file_object_ids = [
            ObjectId(str(note["file_id"]))
            for note in notes
            if note.get("file_id")
            and ObjectId.is_valid(str(note["file_id"]))
        ]

        files_by_id = {}

        if file_object_ids:
            file_cursor = db["files"].find(
                {"_id": {"$in": file_object_ids}}
            )
            file_documents = await file_cursor.to_list(length=None)

            files_by_id = {
                str(file_doc["_id"]): file_doc
                for file_doc in file_documents
            }

        my_notes = []

        for note in notes:
            file_id = str(note.get("file_id", ""))
            file_doc = files_by_id.get(file_id, {})

            my_notes.append({
                "id": str(note["_id"]),
                "title": note.get("title", ""),
                "subject": note.get("subject", ""),
                "description": note.get("description", ""),
                "faculty": note.get("faculty", ""),
                "programme": note.get("programme", ""),
                "semester": note.get("semester", ""),
                "filename": file_doc.get("original_filename", ""),
                "file_url": file_doc.get("secure_url", ""),
                "size": file_doc.get("size", 0),
                "format": file_doc.get("format", ""),
                "created_at": (
                    note["created_at"].isoformat()
                    if note.get("created_at")
                    else None
                ),
            })

        return {
            "total": len(my_notes),
            "notes": my_notes,
        }

    except PyMongoError as exc:
        logger.exception("Failed to retrieve user's uploaded notes")
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve your notes.",
        ) from exc
