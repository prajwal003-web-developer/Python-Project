
from bson import ObjectId
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.db.mongodb import db

programs = db["programs"]
faculties = db["faculties"]


def serialize_program(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "faculty": doc["faculty"],
        "isSemesterWise": doc["isSemesterWise"],
        "total_year": doc["total_year"],
    }


async def validate_faculty(faculty_id: str):
    if not ObjectId.is_valid(faculty_id):
        raise HTTPException(status_code=400, detail="Invalid faculty ID")

    faculty_doc = await faculties.find_one(
        {"_id": ObjectId(faculty_id)}
    )

    if not faculty_doc:
        raise HTTPException(status_code=404, detail="Faculty not found")


async def create_program(data):
    await validate_faculty(data.faculty)

    document = {
        "name": data.name.strip(),
        "faculty": data.faculty,
        "isSemesterWise": data.isSemesterWise,
        "total_year": data.total_year,
    }

    try:
        result = await programs.insert_one(document)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=409,
            detail="This program already exists in the faculty",
        )

    document["_id"] = result.inserted_id
    return serialize_program(document)


async def list_programs():
    cursor = programs.find().sort("name", 1)
    return [serialize_program(doc) async for doc in cursor]


async def update_program(program_id: str, data):
    if not ObjectId.is_valid(program_id):
        raise HTTPException(status_code=400, detail="Invalid program ID")

    updates = data.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    if "name" in updates and updates["name"] is not None:
        updates["name"] = updates["name"].strip()

    if updates.get("faculty") is not None:
        await validate_faculty(updates["faculty"])

    try:
        result = await programs.update_one(
            {"_id": ObjectId(program_id)},
            {"$set": updates},
        )
    except DuplicateKeyError:
        raise HTTPException(
            status_code=409,
            detail="This program already exists in the faculty",
        )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Program not found")

    doc = await programs.find_one({"_id": ObjectId(program_id)})
    return serialize_program(doc)


async def delete_program(program_id: str):
    if not ObjectId.is_valid(program_id):
        raise HTTPException(status_code=400, detail="Invalid program ID")

    result = await programs.delete_one({"_id": ObjectId(program_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Program not found")

    return {"message": "Program deleted successfully"}
