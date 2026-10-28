
from fastapi import APIRouter

from app.endpoints.auth import auth
from app.endpoints.faculty import faculty
from app.endpoints.program import program
from app.endpoints.upload import upload
from app.endpoints.notes import notes

api_router = APIRouter()

api_router.include_router(auth)
api_router.include_router(faculty)
api_router.include_router(program)
api_router.include_router(upload)

api_router.include_router(notes)