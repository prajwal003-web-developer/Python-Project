
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class NoteModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")

    title: str = Field(..., min_length=1, max_length=150)
    description: str = Field(..., max_length=2000)

    faculty: str
    programme: str
    semester: str
    subject: str

    file_id: str
    uploader_id: str

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )
