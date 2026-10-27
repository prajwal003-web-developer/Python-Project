
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class FacultyModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., max_length=500)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )
