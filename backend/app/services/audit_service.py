import logging
from typing import Any

from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase

from app.db.mongodb import Collections as C
from app.models.audit_log import build_audit_document
from app.utils.serialization import utcnow

logger = logging.getLogger("app.audit")


async def record_audit(
    db: AsyncDatabase, actor: dict[str, Any], action: str, target_type: str,
    target_id: ObjectId | None, metadata: dict[str, Any] | None = None,
) -> None:
    """Best-effort: a failed audit write is logged but never fails the already-completed action."""
    try:
        await db[C.AUDIT_LOGS].insert_one(build_audit_document(
            actor_id=actor["_id"], action=action, target_type=target_type,
            target_id=target_id, metadata=metadata, now=utcnow(),
        ))
    except Exception:
        logger.error("Failed to write audit record action=%s target=%s", action, target_id, exc_info=True)
