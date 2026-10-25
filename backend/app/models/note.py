from datetime import datetime
from enum import StrEnum
from typing import Any

from bson import ObjectId


class FileType(StrEnum):
    PDF = "pdf"
    DOCX = "docx"


def build_note_document(
    *, title: str, description: str, subject: str, faculty_id: ObjectId, department_id: ObjectId,
    semester: int, file_type: str, file_url: str, public_id: str, file_size: int,
    uploaded_by: ObjectId, now: datetime,
) -> dict[str, Any]:
    return {
        "title": title, "description": description, "subject": subject,
        "facultyId": faculty_id, "departmentId": department_id, "semester": semester,
        "fileType": file_type, "fileUrl": file_url, "publicId": public_id, "fileSize": file_size,
        "uploadedBy": uploaded_by, "isPublished": True, "hiddenByAdmin": False,
        "createdAt": now, "updatedAt": now,
    }
