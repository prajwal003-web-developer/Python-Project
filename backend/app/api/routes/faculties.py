from fastapi import APIRouter, Query

from app.api.dependencies import Database, OptionalUser
from app.core.permissions import is_admin
from app.schemas.faculty import FacultyOut, faculty_out
from app.services import department_service as svc

router = APIRouter(prefix="/faculties", tags=["Faculties"])


@router.get("", response_model=list[FacultyOut])
async def list_faculties(db: Database, user: OptionalUser, include_inactive: bool = Query(False, alias="includeInactive")):
    """Public. `includeInactive` is honoured only for administrators."""
    docs = await svc.list_faculties(db, include_inactive and user is not None and is_admin(user))
    return [faculty_out(d) for d in docs]


@router.get("/{faculty_id}", response_model=FacultyOut)
async def get_faculty(faculty_id: str, db: Database):
    return faculty_out(await svc.get_faculty(db, faculty_id))
