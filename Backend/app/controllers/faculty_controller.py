
from bson import ObjectId
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.db.mongodb import db

faculties = db["faculties"]
programs = db["programs"]


def serialize_faculty(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "slug": doc["slug"],
        "description": doc.get("description", ""),
    }


def serialize_program(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "faculty": doc["faculty"],
        "isSemesterWise": doc["isSemesterWise"],
        "total_year": doc["total_year"],
    }


async def get_faculties_with_all_data():
    result = []

    async for faculty_doc in faculties.find().sort("name", 1):
        faculty_id = str(faculty_doc["_id"])

        program_cursor = programs.find(
            {"faculty": faculty_id}
        ).sort("name", 1)

        faculty_data = serialize_faculty(faculty_doc)
        faculty_data["programs"] = [
            serialize_program(program_doc)
            async for program_doc in program_cursor
        ]

        result.append(faculty_data)

    return result


async def create_faculty(data):
    document = {
        "name": data.name.strip(),
        "slug": data.slug.strip().lower(),
        "description": data.description.strip(),
    }

    try:
        result = await faculties.insert_one(document)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=409,
            detail="Faculty slug already exists",
        )

    document["_id"] = result.inserted_id
    return serialize_faculty(document)


async def get_faculty_by_id(faculty_id: str):
    if not ObjectId.is_valid(faculty_id):
        raise HTTPException(status_code=400, detail="Invalid faculty ID")

    doc = await faculties.find_one({"_id": ObjectId(faculty_id)})

    if not doc:
        raise HTTPException(status_code=404, detail="Faculty not found")

    return serialize_faculty(doc)


async def update_faculty(faculty_id: str, data):
    if not ObjectId.is_valid(faculty_id):
        raise HTTPException(status_code=400, detail="Invalid faculty ID")

    updates = data.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    for key, value in updates.items():
        if value is not None and isinstance(value, str):
            updates[key] = value.strip()

    if updates.get("slug"):
        updates["slug"] = updates["slug"].lower()

    try:
        result = await faculties.update_one(
            {"_id": ObjectId(faculty_id)},
            {"$set": updates},
        )
    except DuplicateKeyError:
        raise HTTPException(
            status_code=409,
            detail="Faculty slug already exists",
        )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Faculty not found")

    return await get_faculty_by_id(faculty_id)


async def delete_faculty(faculty_id: str):
    if not ObjectId.is_valid(faculty_id):
        raise HTTPException(status_code=400, detail="Invalid faculty ID")

    faculty_oid = ObjectId(faculty_id)

    if not await faculties.find_one({"_id": faculty_oid}):
        raise HTTPException(status_code=404, detail="Faculty not found")

    if await programs.find_one({"faculty": faculty_id}):
        raise HTTPException(
            status_code=409,
            detail="Delete this faculty's programs first",
        )

    await faculties.delete_one({"_id": faculty_oid})

    return {"message": "Faculty deleted successfully"}
