
from fastapi import APIRouter, Depends, Query

from app.controllers.note_controller import (
    get_notes_by_programme_and_semester,
    save_note,
    unsave_note,
    get_saved_notes,
)
from app.controllers.auth_controller import get_current_user

from app.controllers.note_controller import search_notes

notes = APIRouter(prefix="/notes", tags=["Notes"])


# Public: no login required
@notes.get("/")
async def get_notes(
    programme_id: str = Query(...),
    semester: str = Query(..., min_length=1),
):
    return await get_notes_by_programme_and_semester(
        programme_id=programme_id,
        semester=semester,
    )


# Private: get only the logged-in user's saved notes
@notes.get("/saved")
async def read_saved_notes(
    current_user: dict = Depends(get_current_user),
):
    return await get_saved_notes(current_user)


# Private: save a note
@notes.post("/{note_id}/save")
async def save_note_endpoint(
    note_id: str,
    current_user: dict = Depends(get_current_user),
):
    return await save_note(note_id, current_user)


# Private: unsave a note
@notes.delete("/{note_id}/save")
async def unsave_note_endpoint(
    note_id: str,
    current_user: dict = Depends(get_current_user),
):
    return await unsave_note(note_id, current_user)



@notes.get("/search")
async def search_notes_endpoint(
    q: str = Query(..., min_length=1, max_length=100),
):
    return await search_notes(q)