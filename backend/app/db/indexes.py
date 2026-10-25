from pymongo import ASCENDING, DESCENDING, IndexModel
from pymongo.asynchronous.database import AsyncDatabase

from app.db.mongodb import Collections as C


async def create_indexes(db: AsyncDatabase) -> None:
    """Idempotent. Runs on startup and from scripts."""
    await db[C.USERS].create_indexes([
        IndexModel([("normalizedEmail", ASCENDING)], unique=True, name="uniq_normalized_email"),
        IndexModel([("normalizedUsername", ASCENDING)], unique=True, name="uniq_normalized_username"),
        IndexModel([("role", ASCENDING)], name="role"),
        IndexModel([("createdAt", DESCENDING)], name="created_desc"),
    ])
    await db[C.REFRESH_TOKENS].create_indexes([
        IndexModel([("tokenHash", ASCENDING)], unique=True, name="uniq_token_hash"),
        IndexModel([("userId", ASCENDING)], name="user"),
        IndexModel([("familyId", ASCENDING)], name="family"),
        IndexModel([("expiresAt", ASCENDING)], expireAfterSeconds=0, name="ttl_expiry"),
    ])
    await db[C.FACULTIES].create_indexes([
        IndexModel([("slug", ASCENDING)], unique=True, name="uniq_slug"),
        IndexModel([("isActive", ASCENDING), ("name", ASCENDING)], name="active_name"),
    ])
    await db[C.DEPARTMENTS].create_indexes([
        IndexModel([("facultyId", ASCENDING), ("slug", ASCENDING)], unique=True, name="uniq_faculty_slug"),
        IndexModel([("facultyId", ASCENDING), ("isActive", ASCENDING)], name="faculty_active"),
    ])
    await db[C.DEPARTMENT_REQUESTS].create_indexes([
        # At most one *pending* request per faculty+slug (approved/rejected history is preserved)
        IndexModel(
            [("facultyId", ASCENDING), ("slug", ASCENDING)],
            unique=True, partialFilterExpression={"status": "pending"}, name="uniq_pending_request",
        ),
        IndexModel([("status", ASCENDING), ("createdAt", DESCENDING)], name="status_created"),
        IndexModel([("requestedBy", ASCENDING), ("createdAt", DESCENDING)], name="requester_created"),
    ])
    await db[C.NOTES].create_indexes([
        IndexModel([("isPublished", ASCENDING), ("createdAt", DESCENDING)], name="published_created"),
        IndexModel(
            [("facultyId", ASCENDING), ("departmentId", ASCENDING), ("semester", ASCENDING),
             ("isPublished", ASCENDING), ("createdAt", DESCENDING)],
            name="browse_filters",
        ),
        IndexModel([("uploadedBy", ASCENDING), ("createdAt", DESCENDING)], name="uploader_created"),
        IndexModel([("fileType", ASCENDING), ("isPublished", ASCENDING)], name="filetype_published"),
        IndexModel([("title", ASCENDING)], name="title"),
        IndexModel([("departmentId", ASCENDING)], name="department"),
    ])
    await db[C.SAVED_NOTES].create_indexes([
        IndexModel([("userId", ASCENDING), ("noteId", ASCENDING)], unique=True, name="uniq_user_note"),
        IndexModel([("userId", ASCENDING), ("createdAt", DESCENDING)], name="user_created"),
        IndexModel([("noteId", ASCENDING)], name="note"),
    ])
    await db[C.AUDIT_LOGS].create_indexes([
        IndexModel([("createdAt", DESCENDING)], name="created_desc"),
        IndexModel([("actorId", ASCENDING), ("createdAt", DESCENDING)], name="actor_created"),
        IndexModel([("targetId", ASCENDING)], name="target"),
    ])
