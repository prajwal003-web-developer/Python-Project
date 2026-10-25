from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import Database
from app.db.mongodb import Collections as C
from app.schemas.common import Page, PaginationParams, pagination_params
from app.schemas.note import NoteOut, PublicProfile
from app.services import notes_service, user_service

router = APIRouter(prefix="/users", tags=["Public profiles"])


@router.get("/{username}/public", response_model=PublicProfile)
async def public_profile(username: str, db: Database, page: PaginationParams = Depends(pagination_params)):
    """Public. Only name, username, public upload count and published notes are exposed."""
    user = await user_service.get_public_user(db, username)
    count = await db[C.NOTES].count_documents({"uploadedBy": user["_id"], "isPublished": True})
    notes = await notes_service.search_public_notes(db, page, uploaded_by=user["_id"])
    return PublicProfile(name=user["name"], username=user["username"], public_upload_count=count, notes=notes)


@router.get("/{username}/notes", response_model=Page[NoteOut])
async def user_notes(
    username: str, db: Database, page: PaginationParams = Depends(pagination_params),
    q: str | None = Query(None, max_length=100),
    sort_by: str = Query("createdAt", alias="sortBy"),
    sort_order: Literal["asc", "desc"] = Query("desc", alias="sortOrder"),
):
    user = await user_service.get_public_user(db, username)
    return await notes_service.search_public_notes(
        db, page, q=q, uploaded_by=user["_id"], sort_by=sort_by, sort_order=sort_order
    )
