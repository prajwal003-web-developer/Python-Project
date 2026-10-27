
from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MONGODB_URL: str
    DATABASE_NAME: str = "adtu_notes"

    # JWT authentication settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 6000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

client = AsyncMongoClient(settings.MONGODB_URL)
db = client[settings.DATABASE_NAME]


async def connect_to_mongo():
    try:
        # Check MongoDB connection
        await client.admin.command("ping")

        # User indexes
        await db["users"].create_index(
            "email",
            unique=True,
        )
        await db["users"].create_index(
            "username",
            unique=True,
        )

        # Faculty indexes
        await db["faculties"].create_index(
            "slug",
            unique=True,
        )

        # Program names must be unique within each faculty
        await db["programs"].create_index(
            [("faculty", 1), ("name", 1)],
            unique=True,
        )

        print("MongoDB connected successfully!")
        print("Database indexes created successfully!")

    except PyMongoError as exc:
        print(f"MongoDB connection failed: {exc}")
        raise


async def close_mongo_connection():
    await client.close()
    print("MongoDB connection closed.")
