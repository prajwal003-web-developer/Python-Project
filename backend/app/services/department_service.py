from typing import Any

from bson import ObjectId
from pymongo import DESCENDING, ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.db.mongodb import Collections as C
from app.models.audit_log import AuditAction
from app.models.department import build_department_document
from app.models.department_request import RequestStatus, build_request_document
from app.models.faculty import build_faculty_document
from app.schemas.common import PaginationParams, build_page
from app.schemas.department import (
    DepartmentCreate, DepartmentRequestCreate, DepartmentUpdate, request_out,
)
from app.schemas.faculty import FacultyCreate, FacultyUpdate
from app.services.audit_service import record_audit
from app.utils.serialization import parse_object_id, utcnow
from app.utils.text import slugify

Doc = dict[str, Any]
MAX_PENDING_PER_USER = 10


def _slug(name: str) -> str:
    try:
        return slugify(name)
    except ValueError as exc:
        raise BadRequestError("invalid_name", str(exc)) from exc


# ======================= faculties =======================
async def list_faculties(db: AsyncDatabase, include_inactive: bool = False) -> list[Doc]:
    query = {} if include_inactive else {"isActive": True}
    return await db[C.FACULTIES].find(query).sort("name", 1).to_list(None)


async def get_faculty(db: AsyncDatabase, faculty_id: str, *, active_only: bool = True) -> Doc:
    query: Doc = {"_id": parse_object_id(faculty_id, "faculty id")}
    if active_only:
        query["isActive"] = True
    faculty = await db[C.FACULTIES].find_one(query)
    if not faculty:
        raise NotFoundError("faculty_not_found", "Faculty not found")
    return faculty


async def _assert_faculty_removable(db: AsyncDatabase, faculty_id: ObjectId) -> None:
    if await db[C.DEPARTMENTS].count_documents({"facultyId": faculty_id, "isActive": True}, limit=1):
        raise ConflictError("faculty_has_departments", "Remove or deactivate this faculty's departments first")
    if await db[C.NOTES].count_documents({"facultyId": faculty_id}, limit=1):
        raise ConflictError("faculty_has_notes", "This faculty still has notes attached to it")


async def create_faculty(db: AsyncDatabase, admin: Doc, data: FacultyCreate) -> Doc:
    doc = build_faculty_document(name=data.name, slug=_slug(data.name), description=data.description, now=utcnow())
    try:
        await db[C.FACULTIES].insert_one(doc)
    except DuplicateKeyError as exc:
        raise ConflictError("faculty_exists", "A faculty with this name already exists") from exc
    await record_audit(db, admin, AuditAction.FACULTY_CREATE, "faculty", doc["_id"], {"name": doc["name"]})
    return doc


async def update_faculty(db: AsyncDatabase, admin: Doc, faculty_id: str, data: FacultyUpdate) -> Doc:
    faculty = await get_faculty(db, faculty_id, active_only=False)
    changes = data.model_dump(exclude_unset=True)
    updates: Doc = {}
    if "name" in changes:
        updates["name"], updates["slug"] = changes["name"], _slug(changes["name"])
    if "description" in changes:
        updates["description"] = changes["description"]
    if "is_active" in changes:
        if changes["is_active"] is False and faculty.get("isActive", True):
            await _assert_faculty_removable(db, faculty["_id"])
        updates["isActive"] = changes["is_active"]
    updates["updatedAt"] = utcnow()
    try:
        updated = await db[C.FACULTIES].find_one_and_update(
            {"_id": faculty["_id"]}, {"$set": updates}, return_document=ReturnDocument.AFTER
        )
    except DuplicateKeyError as exc:
        raise ConflictError("faculty_exists", "A faculty with this name already exists") from exc
    await record_audit(db, admin, AuditAction.FACULTY_UPDATE, "faculty", faculty["_id"],
                       {"fields": sorted(k for k in updates if k != "updatedAt")})
    return updated


async def delete_faculty(db: AsyncDatabase, admin: Doc, faculty_id: str) -> None:
    """Soft delete (isActive=false). Refused while departments or notes still reference it."""
    faculty = await get_faculty(db, faculty_id, active_only=False)
    await _assert_faculty_removable(db, faculty["_id"])
    await db[C.FACULTIES].update_one({"_id": faculty["_id"]}, {"$set": {"isActive": False, "updatedAt": utcnow()}})
    await record_audit(db, admin, AuditAction.FACULTY_DELETE, "faculty", faculty["_id"], {"name": faculty["name"]})


# ======================= departments =======================
async def list_departments(db: AsyncDatabase, faculty_id: str | None, include_inactive: bool = False) -> list[Doc]:
    query: Doc = {} if include_inactive else {"isActive": True}
    if faculty_id:
        query["facultyId"] = parse_object_id(faculty_id, "faculty id")
    return await db[C.DEPARTMENTS].find(query).sort("name", 1).to_list(None)


async def get_department(db: AsyncDatabase, department_id: str, *, active_only: bool = True) -> Doc:
    query: Doc = {"_id": parse_object_id(department_id, "department id")}
    if active_only:
        query["isActive"] = True
    dept = await db[C.DEPARTMENTS].find_one(query)
    if not dept:
        raise NotFoundError("department_not_found", "Department not found")
    return dept


async def create_department(db: AsyncDatabase, admin: Doc, data: DepartmentCreate) -> Doc:
    faculty = await get_faculty(db, data.faculty_id)
    doc = build_department_document(name=data.name, slug=_slug(data.name), faculty_id=faculty["_id"],
                                    description=data.description, now=utcnow())
    try:
        await db[C.DEPARTMENTS].insert_one(doc)
    except DuplicateKeyError as exc:
        raise ConflictError("department_exists", "This faculty already has a department with this name") from exc
    await record_audit(db, admin, AuditAction.DEPARTMENT_CREATE, "department", doc["_id"],
                       {"name": doc["name"], "facultyId": str(faculty["_id"])})
    return doc


async def update_department(db: AsyncDatabase, admin: Doc, department_id: str, data: DepartmentUpdate) -> Doc:
    dept = await get_department(db, department_id, active_only=False)
    changes = data.model_dump(exclude_unset=True)
    updates: Doc = {}
    if "name" in changes:
        updates["name"], updates["slug"] = changes["name"], _slug(changes["name"])
    if "description" in changes:
        updates["description"] = changes["description"]
    if "is_active" in changes:
        if changes["is_active"] is False and dept.get("isActive", True):
            await _assert_department_removable(db, dept["_id"])
        elif changes["is_active"] is True:
            await get_faculty(db, str(dept["facultyId"]))  # cannot reactivate under an inactive faculty
        updates["isActive"] = changes["is_active"]
    updates["updatedAt"] = utcnow()
    try:
        updated = await db[C.DEPARTMENTS].find_one_and_update(
            {"_id": dept["_id"]}, {"$set": updates}, return_document=ReturnDocument.AFTER
        )
    except DuplicateKeyError as exc:
        raise ConflictError("department_exists", "This faculty already has a department with this name") from exc
    await record_audit(db, admin, AuditAction.DEPARTMENT_UPDATE, "department", dept["_id"],
                       {"fields": sorted(k for k in updates if k != "updatedAt")})
    return updated


async def _assert_department_removable(db: AsyncDatabase, department_id: ObjectId) -> None:
    if await db[C.NOTES].count_documents({"departmentId": department_id}, limit=1):
        raise ConflictError("department_has_notes", "This department still has notes attached to it")


async def delete_department(db: AsyncDatabase, admin: Doc, department_id: str) -> None:
    dept = await get_department(db, department_id, active_only=False)
    await _assert_department_removable(db, dept["_id"])
    await db[C.DEPARTMENTS].update_one({"_id": dept["_id"]}, {"$set": {"isActive": False, "updatedAt": utcnow()}})
    await record_audit(db, admin, AuditAction.DEPARTMENT_DELETE, "department", dept["_id"], {"name": dept["name"]})


# ======================= department requests =======================
async def create_request(db: AsyncDatabase, user: Doc, data: DepartmentRequestCreate) -> Doc:
    faculty = await get_faculty(db, data.faculty_id)
    slug = _slug(data.name)
    requests = db[C.DEPARTMENT_REQUESTS]

    if await db[C.DEPARTMENTS].find_one({"facultyId": faculty["_id"], "slug": slug}, projection={"_id": 1}):
        raise ConflictError("department_exists", "This department already exists in the selected faculty")
    if await requests.find_one({"facultyId": faculty["_id"], "slug": slug, "status": RequestStatus.PENDING.value},
                               projection={"_id": 1}):
        raise ConflictError("request_pending", "A request for this department is already pending")
    if await requests.count_documents({"requestedBy": user["_id"], "status": RequestStatus.PENDING.value}) \
            >= MAX_PENDING_PER_USER:
        raise ConflictError("too_many_pending_requests", "You have too many pending requests")

    doc = build_request_document(name=data.name, slug=slug, faculty_id=faculty["_id"], description=data.description,
                                 requested_by=user["_id"], now=utcnow())
    try:
        await requests.insert_one(doc)  # partial unique index closes the race window
    except DuplicateKeyError as exc:
        raise ConflictError("request_pending", "A request for this department is already pending") from exc
    return doc


async def list_requests(
    db: AsyncDatabase, page: PaginationParams, *, requested_by: ObjectId | None = None,
    status: RequestStatus | None = None, faculty_id: str | None = None, with_requester: bool = False,
) -> dict[str, Any]:
    query: Doc = {}
    if requested_by:
        query["requestedBy"] = requested_by
    if status:
        query["status"] = status.value
    if faculty_id:
        query["facultyId"] = parse_object_id(faculty_id, "faculty id")
    col = db[C.DEPARTMENT_REQUESTS]
    total = await col.count_documents(query)
    docs = await col.find(query).sort("createdAt", DESCENDING).skip(page.skip).limit(page.limit).to_list(None)
    names: dict[ObjectId, str] = {}
    if with_requester and docs:
        users = await db[C.USERS].find({"_id": {"$in": list({d["requestedBy"] for d in docs})}},
                                       projection={"username": 1}).to_list(None)
        names = {u["_id"]: u["username"] for u in users}
    items = [request_out(d, names.get(d["requestedBy"])) for d in docs]
    return build_page(items, total, page.page, page.limit)


async def get_request(db: AsyncDatabase, request_id: str) -> Doc:
    doc = await db[C.DEPARTMENT_REQUESTS].find_one({"_id": parse_object_id(request_id, "request id")})
    if not doc:
        raise NotFoundError("request_not_found", "Department request not found")
    return doc


async def _claim(db: AsyncDatabase, request_id: str, admin: Doc, status: RequestStatus,
                 comment: str | None) -> Doc:
    """Atomically move pending -> approved/rejected so two admins cannot both review it."""
    now = utcnow()
    claimed = await db[C.DEPARTMENT_REQUESTS].find_one_and_update(
        {"_id": parse_object_id(request_id, "request id"), "status": RequestStatus.PENDING.value},
        {"$set": {"status": status.value, "adminComment": comment, "reviewedBy": admin["_id"],
                  "reviewedAt": now, "updatedAt": now}},
        return_document=ReturnDocument.AFTER,
    )
    if claimed:
        return claimed
    await get_request(db, request_id)  # 404 if it does not exist at all
    raise ConflictError("request_already_reviewed", "This request has already been reviewed")


async def approve_request(db: AsyncDatabase, admin: Doc, request_id: str, comment: str | None) -> Doc:
    claimed = await _claim(db, request_id, admin, RequestStatus.APPROVED, comment)
    requests = db[C.DEPARTMENT_REQUESTS]
    try:
        faculty = await get_faculty(db, str(claimed["facultyId"]))
        dept = build_department_document(name=claimed["name"], slug=claimed["slug"], faculty_id=faculty["_id"],
                                         description=claimed.get("description", ""), now=utcnow())
        await db[C.DEPARTMENTS].insert_one(dept)
    except Exception as exc:
        # Roll the request back to pending so nothing is lost, then report why.
        await requests.update_one({"_id": claimed["_id"]}, {"$set": {
            "status": RequestStatus.PENDING.value, "adminComment": None, "reviewedBy": None,
            "reviewedAt": None, "updatedAt": utcnow()}})
        if isinstance(exc, DuplicateKeyError):
            raise ConflictError("department_exists", "This department already exists in the faculty") from exc
        raise
    claimed = await requests.find_one_and_update(
        {"_id": claimed["_id"]}, {"$set": {"departmentId": dept["_id"]}}, return_document=ReturnDocument.AFTER)
    await record_audit(db, admin, AuditAction.REQUEST_APPROVE, "department_request", claimed["_id"],
                       {"departmentId": str(dept["_id"]), "name": dept["name"]})
    return claimed


async def reject_request(db: AsyncDatabase, admin: Doc, request_id: str, comment: str | None) -> Doc:
    claimed = await _claim(db, request_id, admin, RequestStatus.REJECTED, comment)
    await record_audit(db, admin, AuditAction.REQUEST_REJECT, "department_request", claimed["_id"],
                       {"name": claimed["name"]})
    return claimed
