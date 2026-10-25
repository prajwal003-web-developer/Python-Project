from typing import Literal

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from app.api.dependencies import CurrentUser, Database, OptionalUser, UploaderUser
from app.core.rate_limit import upload_limiter
from app.schemas.common import MessageResponse, Page, PaginationParams, pagination_params
from app.schemas.note import MyNotesResponse, NoteCreate, NoteOut, NoteUpdate, note_create_form
from app.services import notes_service as svc

router = APIRouter(prefix="/notes", tags=["Notes"])

# GET "/mine" is declared before GET "/{note_id}" so "mine" is never parsed as a note id.


@router.post("", response_model=NoteOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(upload_limiter)])
async def upload_note(
    user: UploaderUser, db: Database, data: NoteCreate = Depends(note_create_form),
    file: UploadFile = File(..., description="PDF or DOCX"),
):
    """multipart/form-data: title, subject, facultyId, departmentId, semester, description?, file."""
    return await svc.hydrate_note(db, await svc.create_note(db, user, data, file))


@router.get("/mine", response_model=MyNotesResponse)
async def my_notes(
    user: UploaderUser, db: Database, page: PaginationParams = Depends(pagination_params),
    q: str | None = Query(None, max_length=100), file_type: Literal["pdf", "docx"] | None = Query(None, alias="fileType"),
    sort_by: str = Query("createdAt", alias="sortBy"), sort_order: Literal["asc", "desc"] = Query("desc", alias="sortOrder"),
):
    return await svc.my_notes(db, user, page, q=q, file_type=file_type, sort_by=sort_by, sort_order=sort_order)


@router.get("", response_model=Page[NoteOut])
async def search_notes(
    db: Database, page: PaginationParams = Depends(pagination_params),
    q: str | None = Query(None, max_length=100, description="Matches title, description and subject"),
    faculty_id: str | None = Query(None, alias="facultyId"),
    department_id: str | None = Query(None, alias="departmentId"),
    semester: int | None = Query(None, ge=1, le=100),
    username: str | None = Query(None, max_length=30),
    file_type: Literal["pdf", "docx"] | None = Query(None, alias="fileType"),
    sort_by: str = Query("createdAt", alias="sortBy"),
    sort_order: Literal["asc", "desc"] = Query("desc", alias="sortOrder"),
):
    """Public: paginated, filterable library of published notes. No login required."""
    return await svc.search_public_notes(
        db, page, q=q, faculty_id=faculty_id, department_id=department_id, semester=semester,
        username=username, file_type=file_type, sort_by=sort_by, sort_order=sort_order,
    )


@router.get("/{note_id}", response_model=NoteOut)
async def get_note(note_id: str, db: Database, user: OptionalUser):
    """Public for published notes. Unpublished notes are visible only to the owner and admins."""
    return await svc.hydrate_note(db, await svc.get_visible_note(db, note_id, user))


@router.patch("/{note_id}", response_model=NoteOut)
async def update_note(note_id: str, payload: NoteUpdate, user: CurrentUser, db: Database):
    """Owner (uploader) edits metadata; an admin may only publish/unpublish (moderation)."""
    return await svc.hydrate_note(db, await svc.update_note(db, user, note_id, payload))


@router.put("/{note_id}/file", response_model=NoteOut, dependencies=[Depends(upload_limiter)])
async def replace_note_file(note_id: str, user: CurrentUser, db: Database, file: UploadFile = File(...)):
    return await svc.hydrate_note(db, await svc.replace_file(db, user, note_id, file))


@router.delete("/{note_id}", response_model=MessageResponse)
async def delete_note(note_id: str, user: CurrentUser, db: Database):
    await svc.delete_note(db, user, note_id)
    return MessageResponse(message="Note deleted")
