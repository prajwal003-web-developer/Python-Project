from dataclasses import dataclass
from math import ceil
from typing import Any, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

MAX_PAGE_SIZE = 50
T = TypeVar("T")


class CamelModel(BaseModel):
    """JSON uses camelCase (matches the React frontend); Python code uses snake_case."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class MessageResponse(CamelModel):
    message: str


class ErrorDetail(CamelModel):
    field: str
    message: str


class ErrorBody(CamelModel):
    code: str
    message: str
    details: list[ErrorDetail] | None = None


class ErrorResponse(CamelModel):
    error: ErrorBody


class Page(CamelModel, Generic[T]):
    items: list[T]
    page: int
    limit: int
    total: int
    total_pages: int


def build_page(items: list[Any], total: int, page: int, limit: int) -> dict[str, Any]:
    return {"items": items, "page": page, "limit": limit, "total": total,
            "totalPages": ceil(total / limit) if total else 0}


@dataclass(frozen=True)
class PaginationParams:
    page: int
    limit: int

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.limit


def pagination_params(
    page: int = Query(1, ge=1, le=100_000),
    limit: int = Query(20, ge=1, le=MAX_PAGE_SIZE),
) -> PaginationParams:
    return PaginationParams(page=page, limit=limit)
