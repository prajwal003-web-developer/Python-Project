"""Seed sample faculties and departments (idempotent; safe to re-run).

Run from backend/:   python -m scripts.seed_data
Edit SAMPLE below to match your institution.
"""
import asyncio

from dotenv import load_dotenv
from pymongo import AsyncMongoClient

from app.core.config import get_settings
from app.db.indexes import create_indexes
from app.db.mongodb import Collections as C
from app.models.department import build_department_document
from app.models.faculty import build_faculty_document
from app.utils.serialization import utcnow
from app.utils.text import slugify

SAMPLE: dict[str, list[str]] = {
    "Engineering & Technology": [
        "Computer Science & Engineering", "Electronics & Communication Engineering",
        "Mechanical Engineering", "Civil Engineering", "Electrical Engineering",
    ],
    "Science": ["Physics", "Chemistry", "Mathematics"],
    "Management": ["Business Administration", "Commerce"],
    "Humanities & Social Sciences": ["English", "Economics"],
}


async def main() -> None:
    settings = get_settings()
    client = AsyncMongoClient(settings.mongodb_url.get_secret_value(), tz_aware=True, serverSelectionTimeoutMS=5000)
    try:
        db = client[settings.mongodb_db_name]
        await create_indexes(db)
        created_f = created_d = 0
        for faculty_name, departments in SAMPLE.items():
            now = utcnow()
            res = await db[C.FACULTIES].update_one(
                {"slug": slugify(faculty_name)},
                {"$setOnInsert": build_faculty_document(name=faculty_name, slug=slugify(faculty_name),
                                                        description="", now=now)},
                upsert=True,
            )
            created_f += res.upserted_id is not None
            faculty = await db[C.FACULTIES].find_one({"slug": slugify(faculty_name)})
            for dept_name in departments:
                res = await db[C.DEPARTMENTS].update_one(
                    {"facultyId": faculty["_id"], "slug": slugify(dept_name)},
                    {"$setOnInsert": build_department_document(
                        name=dept_name, slug=slugify(dept_name), faculty_id=faculty["_id"], description="", now=now)},
                    upsert=True,
                )
                created_d += res.upserted_id is not None
        print(f"Seed complete: {created_f} faculties and {created_d} departments created (existing ones kept).")
    finally:
        await client.close()


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
