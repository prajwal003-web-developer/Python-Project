
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class FileModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")

    cloudinary_id: str = Field(..., min_length=1)
    size: int = Field(..., ge=0)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )
