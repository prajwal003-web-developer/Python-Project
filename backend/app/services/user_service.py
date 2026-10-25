from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.core.exceptions import NotFoundError
from app.core.security import normalize_username
from app.db.mongodb import Collections as C

Doc = dict[str, Any]


async def get_public_user(db: AsyncDatabase, username: str) -> Doc:
    user = await db[C.USERS].find_one(
        {"normalizedUsername": normalize_username(username), "isActive": True},
        projection={"name": 1, "username": 1},
    )
    if not user:
        raise NotFoundError("user_not_found", "User not found")
    return user
