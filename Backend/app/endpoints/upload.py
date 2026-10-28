from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.controllers.auth_controller import get_current_user
from app.controllers.upload_controller import upload_note_file


upload = APIRouter(prefix="/upload", tags=["File Upload"])


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