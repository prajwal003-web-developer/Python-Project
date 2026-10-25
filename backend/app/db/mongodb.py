from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import Settings


class Collections:
    USERS = "users"
    REFRESH_TOKENS = "refresh_tokens"
    FACULTIES = "faculties"
    DEPARTMENTS = "departments"
    DEPARTMENT_REQUESTS = "department_requests"
    NOTES = "notes"
    SAVED_NOTES = "saved_notes"
    AUDIT_LOGS = "audit_logs"


class MongoManager:
    def __init__(self) -> None:
        self._client: AsyncMongoClient | None = None
        self._db: AsyncDatabase | None = None

    async def connect(self, settings: Settings) -> None:
        self._client = AsyncMongoClient(
            settings.mongodb_url.get_secret_value(),
            tz_aware=True,  # datetimes come back timezone-aware (UTC)
            serverSelectionTimeoutMS=5000,
            appname="adtu-notes-api",
        )
        await self._client.admin.command("ping")
        self._db = self._client[settings.mongodb_db_name]

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
        self._client = None
        self._db = None

    @property
    def database(self) -> AsyncDatabase:
        if self._db is None:
            raise RuntimeError("MongoDB is not connected")
        return self._db


mongo = MongoManager()


def get_db() -> AsyncDatabase:
    """FastAPI dependency. Tests override this with an isolated test database."""
    return mongo.database
