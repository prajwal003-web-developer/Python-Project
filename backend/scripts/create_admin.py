"""Create the first administrator from environment variables.

Run from the backend/ directory:
    python -m scripts.create_admin            # create the first admin
    python -m scripts.create_admin --promote  # promote an EXISTING account (matching ADMIN_EMAIL)

Reads ADMIN_NAME, ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD (see .env.example).
Safe to re-run: if any administrator already exists it does nothing.
"""
import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv  # installed with uvicorn[standard]
from email_validator import EmailNotValidError, validate_email
from pymongo import AsyncMongoClient
from pymongo.errors import DuplicateKeyError

from app.core.config import get_settings
from app.core.security import hash_password, normalize_username, validate_password_strength
from app.db.indexes import create_indexes
from app.db.mongodb import Collections as C
from app.models.user import UserRole, build_user_document
from app.schemas.user import clean_name, clean_username
from app.utils.serialization import utcnow


def _read_credentials() -> tuple[str, str, str, str]:
    missing = [k for k in ("ADMIN_NAME", "ADMIN_USERNAME", "ADMIN_EMAIL", "ADMIN_PASSWORD") if not os.getenv(k)]
    if missing:
        sys.exit(f"Missing environment variables: {', '.join(missing)}")
    try:
        email = validate_email(os.environ["ADMIN_EMAIL"], check_deliverability=False).normalized.lower()
        return (
            clean_name(os.environ["ADMIN_NAME"]),
            # "admin"-style names are reserved for public registration only, so bypass nothing here:
            clean_username(os.environ["ADMIN_USERNAME"]),
            email,
            validate_password_strength(os.environ["ADMIN_PASSWORD"]),
        )
    except (ValueError, EmailNotValidError) as exc:
        sys.exit(f"Invalid admin credentials: {exc}")


async def run(promote: bool) -> int:
    name, username, email, password = _read_credentials()
    settings = get_settings()
    client = AsyncMongoClient(settings.mongodb_url.get_secret_value(), tz_aware=True, serverSelectionTimeoutMS=5000)
    try:
        db = client[settings.mongodb_db_name]
        await create_indexes(db)
        users = db[C.USERS]

        if await users.count_documents({"role": UserRole.ADMIN.value}, limit=1):
            print("An administrator already exists. Nothing to do.")
            return 0

        existing = await users.find_one({"normalizedEmail": email})
        if existing:
            if not promote:
                print(f"A user with {email} already exists. Re-run with --promote to make them admin.")
                return 1
            await users.update_one(
                {"_id": existing["_id"]},
                {"$set": {"role": UserRole.ADMIN.value, "isActive": True, "updatedAt": utcnow()}},
            )
            print(f"Promoted existing user {email} to admin.")
            return 0

        doc = build_user_document(
            name=name, username=username, email=email, normalized_email=email,
            normalized_username=normalize_username(username), password_hash=hash_password(password),
            now=utcnow(), role=UserRole.ADMIN,
        )
        try:
            await users.insert_one(doc)
        except DuplicateKeyError:
            print("That username or email is already taken. Choose different ADMIN_* values.")
            return 1
        print(f"Administrator created: {email}")
        return 0
    finally:
        await client.close()


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--promote", action="store_true", help="promote an existing user with ADMIN_EMAIL")
    sys.exit(asyncio.run(run(parser.parse_args().promote)))
