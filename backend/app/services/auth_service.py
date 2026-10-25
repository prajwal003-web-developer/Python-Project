import asyncio
import uuid
from dataclasses import dataclass
from typing import Any

from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, UnauthorizedError
from app.core.security import (
    ACCESS, DUMMY_HASH, REFRESH, create_access_token, create_refresh_token, decode_token,
    generate_csrf_token, hash_password, hash_token, normalize_email, normalize_username,
    password_needs_rehash, verify_password,
)
from app.db.mongodb import Collections as C
from app.models.user import build_user_document
from app.schemas.auth import RegisterRequest
from app.schemas.user import ProfileUpdate
from app.utils.serialization import utcnow

User = dict[str, Any]


@dataclass
class SessionTokens:
    access: str
    refresh: str
    csrf_token: str


def _conflict(email: bool = False, username: bool = False) -> ConflictError:
    details = []
    if email:
        details.append({"field": "email", "message": "This email is already registered"})
    if username:
        details.append({"field": "username", "message": "This username is already taken"})
    return ConflictError("duplicate_account", "Account already exists", details=details)


# ---------- registration ----------
async def register_user(db: AsyncDatabase, data: RegisterRequest) -> User:
    users = db[C.USERS]
    n_email = normalize_email(data.email)
    n_username = normalize_username(data.username)

    clash = await users.find(
        {"$or": [{"normalizedEmail": n_email}, {"normalizedUsername": n_username}]},
        projection={"normalizedEmail": 1, "normalizedUsername": 1},
    ).to_list(2)
    if clash:
        raise _conflict(
            email=any(u["normalizedEmail"] == n_email for u in clash),
            username=any(u["normalizedUsername"] == n_username for u in clash),
        )

    doc = build_user_document(
        name=data.name, username=data.username, email=n_email, normalized_email=n_email,
        normalized_username=n_username, password_hash=await asyncio.to_thread(hash_password, data.password),
        now=utcnow(),
    )
    try:
        await users.insert_one(doc)  # sets doc["_id"]
    except DuplicateKeyError as exc:  # race between the check above and the insert
        pattern = (getattr(exc, "details", None) or {}).get("keyPattern", {})
        raise _conflict(email="normalizedEmail" in pattern, username="normalizedUsername" in pattern) from exc
    return doc


# ---------- login ----------
async def authenticate(db: AsyncDatabase, email: str, password: str) -> User:
    users = db[C.USERS]
    user = await users.find_one({"normalizedEmail": normalize_email(email)})
    ok = await asyncio.to_thread(verify_password, user["passwordHash"] if user else DUMMY_HASH, password)
    if not user or not ok:
        raise UnauthorizedError("invalid_credentials", "Invalid email or password")
    if not user.get("isActive", True):
        raise ForbiddenError("account_disabled", "This account has been disabled")
    if password_needs_rehash(user["passwordHash"]):
        new_hash = await asyncio.to_thread(hash_password, password)
        await users.update_one({"_id": user["_id"]}, {"$set": {"passwordHash": new_hash}})
    return user


# ---------- sessions / refresh tokens ----------
async def create_session(
    db: AsyncDatabase, user: User, *, family_id: str | None = None,
    user_agent: str | None = None, csrf_token: str | None = None,
) -> SessionTokens:
    user_id = str(user["_id"])
    access, _ = create_access_token(user_id)
    refresh, expires = create_refresh_token(user_id)
    await db[C.REFRESH_TOKENS].insert_one({
        "userId": user["_id"],
        "familyId": family_id or uuid.uuid4().hex,
        "tokenHash": hash_token(refresh),
        "expiresAt": expires,
        "createdAt": utcnow(),
        "revokedAt": None,
        "userAgent": (user_agent or "")[:200],
    })
    return SessionTokens(access, refresh, csrf_token or generate_csrf_token())


async def _revoke_family(db: AsyncDatabase, family_id: str) -> None:
    await db[C.REFRESH_TOKENS].update_many(
        {"familyId": family_id, "revokedAt": None}, {"$set": {"revokedAt": utcnow()}}
    )


async def rotate_session(
    db: AsyncDatabase, refresh_token: str, *, user_agent: str | None = None, csrf_token: str | None = None,
) -> tuple[User, SessionTokens]:
    """Single-use refresh tokens. Re-presenting a used token revokes the whole token family."""
    decode_token(refresh_token, REFRESH)
    tokens = db[C.REFRESH_TOKENS]
    record = await tokens.find_one({"tokenHash": hash_token(refresh_token)})
    if not record:
        raise UnauthorizedError("invalid_token", "Invalid or expired token")

    claimed = await tokens.update_one(
        {"_id": record["_id"], "revokedAt": None}, {"$set": {"revokedAt": utcnow()}}
    )
    if claimed.modified_count == 0:  # already used/revoked -> possible theft
        await _revoke_family(db, record["familyId"])
        raise UnauthorizedError("token_reuse_detected", "Session is no longer valid. Please log in again")

    user = await db[C.USERS].find_one({"_id": record["userId"]})
    if not user or not user.get("isActive", True):
        await _revoke_family(db, record["familyId"])
        raise UnauthorizedError("invalid_token", "Invalid or expired token")

    session = await create_session(
        db, user, family_id=record["familyId"], user_agent=user_agent, csrf_token=csrf_token
    )
    return user, session


async def revoke_session(db: AsyncDatabase, refresh_token: str | None) -> None:
    """Best-effort logout: never raises."""
    if not refresh_token:
        return
    record = await db[C.REFRESH_TOKENS].find_one({"tokenHash": hash_token(refresh_token)})
    if record:
        await _revoke_family(db, record["familyId"])


async def revoke_all_sessions(db: AsyncDatabase, user_id: ObjectId) -> None:
    await db[C.REFRESH_TOKENS].update_many(
        {"userId": user_id, "revokedAt": None}, {"$set": {"revokedAt": utcnow()}}
    )


# ---------- current user / profile ----------
async def get_user_from_access_token(db: AsyncDatabase, token: str) -> User | None:
    try:
        payload = decode_token(token, ACCESS)
        user_id = ObjectId(payload["sub"])
    except Exception:  # invalid/expired token or malformed subject
        return None
    return await db[C.USERS].find_one({"_id": user_id})


async def update_profile(db: AsyncDatabase, user: User, data: ProfileUpdate) -> tuple[User, bool]:
    """Returns (updated_user, password_changed). Only whitelisted fields can ever be changed."""
    updates: dict[str, Any] = {}
    if data.name is not None:
        updates["name"] = data.name
    if data.username is not None:
        n_username = normalize_username(data.username)
        if n_username != user["normalizedUsername"]:
            if await db[C.USERS].find_one({"normalizedUsername": n_username}, projection={"_id": 1}):
                raise _conflict(username=True)
            updates["username"] = data.username
            updates["normalizedUsername"] = n_username

    password_changed = False
    if data.new_password:
        valid = await asyncio.to_thread(verify_password, user["passwordHash"], data.current_password or "")
        if not valid:
            raise BadRequestError("invalid_current_password", "Current password is incorrect")
        updates["passwordHash"] = await asyncio.to_thread(hash_password, data.new_password)
        password_changed = True

    if not updates:
        return user, False
    updates["updatedAt"] = utcnow()
    try:
        updated = await db[C.USERS].find_one_and_update(
            {"_id": user["_id"]}, {"$set": updates}, return_document=ReturnDocument.AFTER
        )
    except DuplicateKeyError as exc:
        raise _conflict(username=True) from exc
    if password_changed:
        await revoke_all_sessions(db, user["_id"])
    return updated, password_changed

