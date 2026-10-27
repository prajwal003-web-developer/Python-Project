
from fastapi import APIRouter, Depends, status

from app.controllers.faculty_controller import (
    get_faculties_with_all_data,
    create_faculty,
    get_faculty_by_id,
    update_faculty,
    delete_faculty,
)
from app.controllers.auth_controller import require_admin
from app.schemas.academic import FacultyCreate, FacultyUpdate

faculty = APIRouter(prefix="/faculties", tags=["Faculties"])


# PUBLIC: no login required
@faculty.get("/")
async def get_all_faculties():
    return await get_faculties_with_all_data()


# ADMIN ONLY
@faculty.post("/", status_code=status.HTTP_201_CREATED)
async def create(data: FacultyCreate, admin=Depends(require_admin)):
    return await create_faculty(data)


@faculty.get("/{faculty_id}")
async def get_one(
    faculty_id: str,
    admin=Depends(require_admin),
):
    return await get_faculty_by_id(faculty_id)


@faculty.patch("/{faculty_id}")
async def update(
    faculty_id: str,
    data: FacultyUpdate,
    admin=Depends(require_admin),
):
    return await update_faculty(faculty_id, data)


@faculty.delete("/{faculty_id}")
async def delete(
    faculty_id: str,
    admin=Depends(require_admin),
):
    return await delete_faculty(faculty_id)
