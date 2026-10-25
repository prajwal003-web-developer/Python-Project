from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import AdminUser, Database
from app.models.department_request import RequestStatus
from app.models.user import UserRole
from app.schemas.admin import AdminUserOut, DashboardOut, RoleUpdate, StatusUpdate
from app.schemas.common import MessageResponse, Page, PaginationParams, pagination_params
from app.schemas.department import (
    DepartmentCreate, DepartmentOut, DepartmentRequestOut, DepartmentUpdate, RequestDecision,
    department_out, request_out,
)
from app.schemas.faculty import FacultyCreate, FacultyOut, FacultyUpdate, faculty_out
from app.services import admin_service, department_service as svc

router = APIRouter(prefix="/admin", tags=["Admin"])



# ---------------- department requests ----------------
@router.get("/department-requests", response_model=Page[DepartmentRequestOut])
async def list_requests(
    admin: AdminUser, db: Database, page: PaginationParams = Depends(pagination_params),
    status_filter: RequestStatus | None = Query(None, alias="status"),
    faculty_id: str | None = Query(None, alias="facultyId"),
):
    return await svc.list_requests(db, page, status=status_filter, faculty_id=faculty_id, with_requester=True)


@router.get("/department-requests/{request_id}", response_model=DepartmentRequestOut)
async def get_request(request_id: str, admin: AdminUser, db: Database):
    return request_out(await svc.get_request(db, request_id))


@router.patch("/department-requests/{request_id}/approve", response_model=DepartmentRequestOut)
async def approve_request(request_id: str, admin: AdminUser, db: Database, payload: RequestDecision | None = None):
    return request_out(await svc.approve_request(db, admin, request_id, payload.admin_comment if payload else None))


@router.patch("/department-requests/{request_id}/reject", response_model=DepartmentRequestOut)
async def reject_request(request_id: str, admin: AdminUser, db: Database, payload: RequestDecision | None = None):
    return request_out(await svc.reject_request(db, admin, request_id, payload.admin_comment if payload else None))


# ---------------- faculties ----------------
@router.post("/faculties", response_model=FacultyOut, status_code=status.HTTP_201_CREATED)
async def create_faculty(payload: FacultyCreate, admin: AdminUser, db: Database):
    return faculty_out(await svc.create_faculty(db, admin, payload))


@router.patch("/faculties/{faculty_id}", response_model=FacultyOut)
async def update_faculty(faculty_id: str, payload: FacultyUpdate, admin: AdminUser, db: Database):
    return faculty_out(await svc.update_faculty(db, admin, faculty_id, payload))


@router.delete("/faculties/{faculty_id}", response_model=MessageResponse)
async def delete_faculty(faculty_id: str, admin: AdminUser, db: Database):
    """Soft delete. Refused (409) while active departments or notes reference the faculty."""
    await svc.delete_faculty(db, admin, faculty_id)
    return MessageResponse(message="Faculty deleted")


# ---------------- departments ----------------
@router.post("/departments", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
async def create_department(payload: DepartmentCreate, admin: AdminUser, db: Database):
    return department_out(await svc.create_department(db, admin, payload))


@router.patch("/departments/{department_id}", response_model=DepartmentOut)
async def update_department(department_id: str, payload: DepartmentUpdate, admin: AdminUser, db: Database):
    return department_out(await svc.update_department(db, admin, department_id, payload))


@router.delete("/departments/{department_id}", response_model=MessageResponse)
async def delete_department(department_id: str, admin: AdminUser, db: Database):
    """Soft delete. Refused (409) while notes still belong to the department."""
    await svc.delete_department(db, admin, department_id)
    return MessageResponse(message="Department deleted")


# ---------------- users & roles ----------------
@router.get("/users", response_model=Page[AdminUserOut])
async def list_users(
    admin: AdminUser, db: Database, page: PaginationParams = Depends(pagination_params),
    q: str | None = Query(None, max_length=100), role: UserRole | None = Query(None),
    is_active: bool | None = Query(None, alias="isActive"),
):
    return await admin_service.list_users(db, page, q=q, role=role, is_active=is_active)


@router.get("/users/{user_id}", response_model=AdminUserOut)
async def get_user(user_id: str, admin: AdminUser, db: Database):
    return await admin_service.user_detail(db, user_id)


@router.patch("/users/{user_id}/role", response_model=AdminUserOut)
async def change_role(user_id: str, payload: RoleUpdate, admin: AdminUser, db: Database):
    """Promote to `uploader`, revoke back to `user`, or change admin status. The last admin is protected."""
    return await admin_service.change_role(db, admin, user_id, payload.role)


@router.patch("/users/{user_id}/status", response_model=AdminUserOut)
async def change_status(user_id: str, payload: StatusUpdate, admin: AdminUser, db: Database):
    return await admin_service.change_status(db, admin, user_id, payload.is_active)


# ---------------- dashboard ----------------
@router.get("/dashboard", response_model=DashboardOut)
async def dashboard(admin: AdminUser, db: Database):
    return await admin_service.dashboard(db)
