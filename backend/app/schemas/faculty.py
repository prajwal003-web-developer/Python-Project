from datetime import datetime
from typing import Any

from pydantic import ConfigDict, model_validator

from app.schemas.common import CamelModel
from app.schemas.common_types import Description, Name


class FacultyCreate(CamelModel):
    model_config = ConfigDict(extra="forbid")
    name: Name
    description: Description = ""


class FacultyUpdate(CamelModel):
    model_config = ConfigDict(extra="forbid")
    name: Name | None = None
    description: Description | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def _any(self) -> "FacultyUpdate":
        if not self.model_fields_set:
            raise ValueError("No fields to update")
        return self


class FacultyOut(CamelModel):
    id: str
    name: str
    slug: str
    description: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


def faculty_out(d: dict[str, Any]) -> FacultyOut:
    return FacultyOut(id=str(d["_id"]), name=d["name"], slug=d["slug"], description=d.get("description", ""),
                      is_active=d.get("isActive", True), created_at=d["createdAt"], updated_at=d["updatedAt"])
