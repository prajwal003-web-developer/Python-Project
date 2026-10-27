
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class ProgramModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str = Field(..., min_length=1, max_length=100)
    faculty: str  # Faculty document ID
    isSemesterWise: bool = True
    total_year: int = Field(..., ge=1, le=10)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )
