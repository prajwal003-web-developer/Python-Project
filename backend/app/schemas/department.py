from datetime import datetime
from typing import Any

from pydantic import ConfigDict, model_validator

from app.models.department_request import RequestStatus
from app.schemas.common import CamelModel
from app.schemas.common_types import AdminComment, Description, Name


class DepartmentCreate(CamelModel):
    model_config = ConfigDict(extra="forbid")
    name: Name
    faculty_id: str
    description: Description = ""


class DepartmentUpdate(CamelModel):
    model_config = ConfigDict(extra="forbid")
    name: Name | None = None
    description: Description | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def _any(self) -> "DepartmentUpdate":
        if not self.model_fields_set:
            raise ValueError("No fields to update")
        return self


class DepartmentOut(CamelModel):
    id: str
    name: str
    slug: str
    faculty_id: str
    description: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


def department_out(d: dict[str, Any]) -> DepartmentOut:
    return DepartmentOut(
        id=str(d["_id"]), name=d["name"], slug=d["slug"], faculty_id=str(d["facultyId"]),
        description=d.get("description", ""), is_active=d.get("isActive", True),
        created_at=d["createdAt"], updated_at=d["updatedAt"],
    )


class DepartmentRequestCreate(CamelModel):
    model_config = ConfigDict(extra="forbid")  # status/requestedBy can never be client-supplied
    name: Name
    faculty_id: str
    description: Description = ""


class RequestDecision(CamelModel):
    model_config = ConfigDict(extra="forbid")
    admin_comment: AdminComment | None = None


class DepartmentRequestOut(CamelModel):
    id: str
    name: str
    slug: str
    faculty_id: str
    description: str
    requested_by: str
    requester_username: str | None = None
    status: RequestStatus
    admin_comment: str | None
    reviewed_by: str | None
    reviewed_at: datetime | None
    department_id: str | None
    created_at: datetime
    updated_at: datetime


def request_out(d: dict[str, Any], requester_username: str | None = None) -> DepartmentRequestOut:
    return DepartmentRequestOut(
        id=str(d["_id"]), name=d["name"], slug=d["slug"], faculty_id=str(d["facultyId"]),
        description=d.get("description", ""), requested_by=str(d["requestedBy"]),
        requester_username=requester_username, status=RequestStatus(d["status"]),
        admin_comment=d.get("adminComment"),
        reviewed_by=str(d["reviewedBy"]) if d.get("reviewedBy") else None,
        reviewed_at=d.get("reviewedAt"),
        department_id=str(d["departmentId"]) if d.get("departmentId") else None,
        created_at=d["createdAt"], updated_at=d["updatedAt"],
    )
