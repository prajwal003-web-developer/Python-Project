import re
from typing import Any

from bson import ObjectId
from pymongo import DESCENDING, ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.db.mongodb import Collections as C
from app.models.audit_log import AuditAction
from app.models.department_request import RequestStatus
from app.models.user import UserRole
from app.schemas.admin import AuditLogOut, DashboardCounts, DashboardOut, admin_user_out
from app.schemas.common import PaginationParams, build_page
from app.services.audit_service import record_audit
from app.services.auth_service import revoke_all_sessions
from app.utils.serialization import parse_object_id, utcnow

Doc = dict[str, Any]


async def _note_counts(db: AsyncDatabase, user_ids: list[ObjectId]) -> dict[ObjectId, int]:
    if not user_ids:
        return {}
    cursor = await db[C.NOTES].aggregate([
        {"$match": {"uploadedBy": {"$in": user_ids}}},
        {"$group": {"_id": "$uploadedBy", "n": {"$sum": 1}}},
    ])
    return {row["_id"]: row["n"] for row in await cursor.to_list(None)}


async def list_users(
    db: AsyncDatabase, page: PaginationParams, *, q: str | None, role: UserRole | None, is_active: bool | None,
) -> dict[str, Any]:
    query: Doc = {}
    if role:
        query["role"] = role.value
    if is_active is not None:
        query["isActive"] = is_active
    if q:
        rx = {"$regex": re.escape(q.strip()), "$options": "i"}
        query["$or"] = [{"name": rx}, {"username": rx}, {"email": rx}]
    users = db[C.USERS]
    total = await users.count_documents(query)
    docs = await users.find(query, projection={"passwordHash": 0}).sort([("createdAt", DESCENDING), ("_id", DESCENDING)]) \
        .skip(page.skip).limit(page.limit).to_list(None)
    counts = await _note_counts(db, [d["_id"] for d in docs])
    return build_page([admin_user_out(d, counts.get(d["_id"], 0)) for d in docs], total, page.page, page.limit)


async def get_user(db: AsyncDatabase, user_id: str) -> Doc:
    user = await db[C.USERS].find_one({"_id": parse_object_id(user_id, "user id")})
    if not user:
        raise NotFoundError("user_not_found", "User not found")
    return user


async def user_detail(db: AsyncDatabase, user_id: str):
    user = await get_user(db, user_id)
    return admin_user_out(user, (await _note_counts(db, [user["_id"]])).get(user["_id"], 0))


async def _other_active_admin_exists(db: AsyncDatabase, user_id: ObjectId) -> bool:
    return bool(await db[C.USERS].count_documents(
        {"role": UserRole.ADMIN.value, "isActive": True, "_id": {"$ne": user_id}}, limit=1))


async def _no_active_admin(db: AsyncDatabase) -> bool:
    return not await db[C.USERS].count_documents({"role": UserRole.ADMIN.value, "isActive": True}, limit=1)


async def change_role(db: AsyncDatabase, admin: Doc, user_id: str, new_role: UserRole):
    target = await get_user(db, user_id)
    old_role = UserRole(target["role"])
    if new_role == old_role:
        return await user_detail(db, user_id)
    demoting_admin = old_role == UserRole.ADMIN
    if demoting_admin and not await _other_active_admin_exists(db, target["_id"]):
        raise ConflictError("last_admin", "You cannot remove the last administrator")

    await db[C.USERS].update_one({"_id": target["_id"]}, {"$set": {"role": new_role.value, "updatedAt": utcnow()}})
    if demoting_admin and await _no_active_admin(db):  # lost a race with another demotion -> undo
        await db[C.USERS].update_one({"_id": target["_id"]}, {"$set": {"role": old_role.value}})
        raise ConflictError("last_admin", "You cannot remove the last administrator")
    await record_audit(db, admin, AuditAction.USER_ROLE_CHANGE, "user", target["_id"],
                       {"from": old_role.value, "to": new_role.value, "username": target["username"]})
    return await user_detail(db, user_id)


async def change_status(db: AsyncDatabase, admin: Doc, user_id: str, is_active: bool):
    target = await get_user(db, user_id)
    if target["_id"] == admin["_id"] and not is_active:
        raise ForbiddenError("cannot_disable_self", "You cannot deactivate your own account")
    if target.get("isActive", True) == is_active:
        return await user_detail(db, user_id)
    if not is_active and target["role"] == UserRole.ADMIN.value and not await _other_active_admin_exists(db, target["_id"]):
        raise ConflictError("last_admin", "You cannot deactivate the last administrator")

    await db[C.USERS].find_one_and_update(
        {"_id": target["_id"]}, {"$set": {"isActive": is_active, "updatedAt": utcnow()}},
        return_document=ReturnDocument.AFTER)
    if not is_active:
        await revoke_all_sessions(db, target["_id"])  # access tokens are also rejected: isActive is checked per request
    await record_audit(db, admin, AuditAction.USER_STATUS_CHANGE, "user", target["_id"],
                       {"isActive": is_active, "username": target["username"]})
    return await user_detail(db, user_id)


async def dashboard(db: AsyncDatabase) -> DashboardOut:
    users, notes = db[C.USERS], db[C.NOTES]
    counts = DashboardCounts(
        users=await users.count_documents({}),
        uploaders=await users.count_documents({"role": UserRole.UPLOADER.value}),
        admins=await users.count_documents({"role": UserRole.ADMIN.value}),
        notes=await notes.count_documents({}),
        published_notes=await notes.count_documents({"isPublished": True}),
        faculties=await db[C.FACULTIES].count_documents({"isActive": True}),
        departments=await db[C.DEPARTMENTS].count_documents({"isActive": True}),
        pending_department_requests=await db[C.DEPARTMENT_REQUESTS].count_documents(
            {"status": RequestStatus.PENDING.value}),
    )
    logs = await db[C.AUDIT_LOGS].find().sort([("createdAt", DESCENDING), ("_id", DESCENDING)]).limit(20).to_list(None)
    actors = await users.find({"_id": {"$in": list({log["actorId"] for log in logs})}},
                              projection={"username": 1}).to_list(None) if logs else []
    names = {a["_id"]: a["username"] for a in actors}
    recent = [AuditLogOut(
        id=str(log["_id"]), action=log["action"], actor_id=str(log["actorId"]),
        actor_username=names.get(log["actorId"]), target_type=log["targetType"],
        target_id=str(log["targetId"]) if log.get("targetId") else None,
        metadata=log.get("metadata", {}), created_at=log["createdAt"]) for log in logs]
    return DashboardOut(counts=counts, recent_activity=recent)
