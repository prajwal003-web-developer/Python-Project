from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import CurrentUser, Database, OptionalUser
from app.core.permissions import is_admin
from app.core.rate_limit import department_request_limiter
from app.schemas.common import PaginationParams, Page, pagination_params
from app.schemas.department import (
    DepartmentOut, DepartmentRequestCreate, DepartmentRequestOut, department_out, request_out,
)
from app.services import department_service as svc

router = APIRouter(prefix="/departments", tags=["Departments"])


# NOTE: the /requests routes are declared before /{department_id} so they are never shadowed.
@router.post("/requests", response_model=DepartmentRequestOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(department_request_limiter)])
async def create_department_request(payload: DepartmentRequestCreate, user: CurrentUser, db: Database):
    """Authenticated users ask admins to add a department. Status is always `pending`."""
    return request_out(await svc.create_request(db, user, payload))


@router.get("/requests/mine", response_model=Page[DepartmentRequestOut])
async def my_department_requests(user: CurrentUser, db: Database, page: PaginationParams = Depends(pagination_params)):
    return await svc.list_requests(db, page, requested_by=user["_id"])


@router.get("", response_model=list[DepartmentOut])
async def list_departments(
    db: Database, user: OptionalUser, faculty_id: str | None = Query(None, alias="facultyId"),
    include_inactive: bool = Query(False, alias="includeInactive"),
):
    docs = await svc.list_departments(db, faculty_id, include_inactive and user is not None and is_admin(user))
    return [department_out(d) for d in docs]


@router.get("/{department_id}", response_model=DepartmentOut)
async def get_department(department_id: str, db: Database):
    return department_out(await svc.get_department(db, department_id))
