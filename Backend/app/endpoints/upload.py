
from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.controllers.auth_controller import get_current_user


from app.controllers.upload_controller import (
    upload_note_file,
    delete_note,
    get_my_notes,
)

upload = APIRouter(prefix="/upload", tags=["File Upload"])


# Upload a note
@upload.post("/notes", status_code=201)
async def upload_note(
    file: UploadFile = File(...),
    title: str = Form(..., min_length=1, max_length=150),
    description: str = Form("", max_length=2000),
    faculty: str = Form(...),
    programme: str = Form(...),
    semester: str = Form(...),
    subject: str = Form(...),
    current_user: dict = Depends(get_current_user),
):
    return await upload_note_file(
        file=file,
        title=title,
        description=description,
        faculty=faculty,
        programme=programme,
        semester=semester,
        subject=subject,
        current_user=current_user,
    )


# Delete a note uploaded by the logged-in user
@upload.delete("/notes/{note_id}")
async def delete_note_endpoint(
    note_id: str,
    current_user: dict = Depends(get_current_user),
):
    return await delete_note(
        note_id=note_id,
        current_user=current_user,
    )



@upload.get("/my-notes")
async def read_my_notes(
    current_user: dict = Depends(get_current_user),
):
    return await get_my_notes(current_user)
