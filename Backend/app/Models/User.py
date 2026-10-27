
from typing import Optional

from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")

    full_name: str = Field(..., min_length=2, max_length=100)
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    password: str

    is_admin: bool = False

    saved_notes: list[str] = Field(default_factory=list)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )
