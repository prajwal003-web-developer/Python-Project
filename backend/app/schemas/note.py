from datetime import datetime
from typing import Any, Literal

from fastapi import Form
from fastapi.exceptions import RequestValidationError
from pydantic import ConfigDict, Field, ValidationError, model_validator

from app.schemas.common import CamelModel, Page
from app.schemas.common_types import NoteDescription, Subject, Title
from app.schemas.user import PublicUser


class NoteCreate(CamelModel):
    model_config = ConfigDict(extra="forbid")
    title: Title
    description: NoteDescription = ""
    subject: Subject
    faculty_id: str
    department_id: str
    semester: int = Field(ge=1, le=100)  # upper bound re-checked against MAX_SEMESTERS in the service


def note_create_form(
    title: str = Form(...),
    subject: str = Form(...),
    faculty_id: str = Form(..., alias="facultyId"),
    department_id: str = Form(..., alias="departmentId"),
    semester: int = Form(...),
    description: str = Form(""),
) -> NoteCreate:
    """Validates multipart text fields with the same Pydantic rules as JSON bodies."""
    try:
        return NoteCreate(title=title, subject=subject, faculty_id=faculty_id,
                          department_id=department_id, semester=semester, description=description)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors(include_url=False, include_context=False)) from exc


class NoteUpdate(CamelModel):
    model_config = ConfigDict(extra="forbid")  # uploadedBy / role / fileUrl etc. are rejected
    title: Title | None = None
    description: NoteDescription | None = None
    subject: Subject | None = None
    faculty_id: str | None = None
    department_id: str | None = None
    semester: int | None = Field(default=None, ge=1, le=100)
    is_published: bool | None = None

    @model_validator(mode="after")
    def _any(self) -> "NoteUpdate":
        if not self.model_fields_set:
            raise ValueError("No fields to update")
        return self


class NoteOut(CamelModel):
    """Public note shape. No email, no passwordHash, no Cloudinary publicId."""

    id: str
    title: str
    description: str
    subject: str
    faculty_id: str
    faculty_name: str | None
    department_id: str
    department_name: str | None
    semester: int
    file_type: Literal["pdf", "docx"]
    file_url: str
    file_size: int
    is_published: bool
    hidden_by_admin: bool = False
    uploader: PublicUser
    created_at: datetime
    updated_at: datetime


def note_out(doc: dict[str, Any], uploader: dict[str, Any] | None,
             faculty: dict[str, Any] | None, department: dict[str, Any] | None) -> NoteOut:
    return NoteOut(
        id=str(doc["_id"]), title=doc["title"], description=doc.get("description", ""),
        subject=doc["subject"], faculty_id=str(doc["facultyId"]),
        faculty_name=faculty["name"] if faculty else None,
        department_id=str(doc["departmentId"]),
        department_name=department["name"] if department else None,
        semester=doc["semester"], file_type=doc["fileType"], file_url=doc["fileUrl"],
        file_size=doc["fileSize"], is_published=doc.get("isPublished", True),
        hidden_by_admin=doc.get("hiddenByAdmin", False),
        uploader=PublicUser(name=uploader["name"], username=uploader["username"]) if uploader
        else PublicUser(name="Unknown", username="unknown"),
        created_at=doc["createdAt"], updated_at=doc["updatedAt"],
    )


class UploadStats(CamelModel):
    total_notes: int
    published_notes: int
    unpublished_notes: int
    pdf_count: int
    docx_count: int
    total_file_size: int
    first_uploaded_at: datetime | None
    last_uploaded_at: datetime | None


class MyNotesResponse(CamelModel):
    stats: UploadStats
    notes: Page[NoteOut]


class PublicProfile(CamelModel):
    name: str
    username: str
    public_upload_count: int
    notes: Page[NoteOut]


class SavedNoteOut(CamelModel):
    saved_at: datetime
    note: NoteOut


class SavedStatus(CamelModel):
    note_id: str
    saved: bool
