from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import CurrentUser, Database
from app.schemas.common import Page, PaginationParams, pagination_params
from app.schemas.note import SavedNoteOut, SavedStatus
from app.services import saved_notes_service as svc

router = APIRouter(prefix="/saved-notes", tags=["Saved notes"])


@router.get("", response_model=Page[SavedNoteOut])
async def list_saved_notes(user: CurrentUser, db: Database, page: PaginationParams = Depends(pagination_params)):
    """The caller's own saved notes (never anyone else's)."""
    return await svc.list_saved(db, user, page)


@router.post("/{note_id}", response_model=SavedStatus)
async def save_note(note_id: str, response: Response, user: CurrentUser, db: Database):
    """201 when newly saved, 200 when it was already saved."""
    oid, created = await svc.save_note(db, user, note_id)
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return SavedStatus(note_id=str(oid), saved=True)


@router.delete("/{note_id}", response_model=SavedStatus)
async def unsave_note(note_id: str, user: CurrentUser, db: Database):
    return SavedStatus(note_id=str(await svc.unsave_note(db, user, note_id)), saved=False)
