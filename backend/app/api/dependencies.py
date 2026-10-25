from typing import Annotated, Any

from fastapi import Depends, Request
from fastapi.security import APIKeyHeader
from pymongo.asynchronous.database import AsyncDatabase

from app.core.cookies import ACCESS_COOKIE, CSRF_HEADER
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.permissions import can_upload_notes, is_admin
from app.db.mongodb import get_db
from app.services.auth_service import get_user_from_access_token

User = dict[str, Any]

# Only here so Swagger UI shows an "Authorize" box for the CSRF header (cookies are sent by the browser).
csrf_doc_scheme = APIKeyHeader(name=CSRF_HEADER, scheme_name="CSRF", auto_error=False)

Database = Annotated[AsyncDatabase, Depends(get_db)]


async def get_current_user(
    request: Request, db: Database, _csrf: str | None = Depends(csrf_doc_scheme)
) -> User | None:
    """Optional authentication: returns the user document, or None for anonymous/invalid/disabled.

    Public endpoints use this so a stale cookie never breaks anonymous browsing.
    """
    request.state.auth_failure = None
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        return None
    user = await get_user_from_access_token(db, token)
    if user is None:
        request.state.auth_failure = "invalid"
        return None
    if not user.get("isActive", True):
        request.state.auth_failure = "disabled"
        return None
    return user


async def require_authenticated_user(
    request: Request, user: User | None = Depends(get_current_user)
) -> User:
    if user is None:
        if getattr(request.state, "auth_failure", None) == "disabled":
            raise ForbiddenError("account_disabled", "This account has been disabled")
        raise UnauthorizedError()
    return user


async def require_uploader(user: User = Depends(require_authenticated_user)) -> User:
    if not can_upload_notes(user):
        raise ForbiddenError("uploader_required", "Uploader permission is required")
    return user


async def require_admin(user: User = Depends(require_authenticated_user)) -> User:
    if not is_admin(user):
        raise ForbiddenError("admin_required", "Administrator permission is required")
    return user


OptionalUser = Annotated[User | None, Depends(get_current_user)]
CurrentUser = Annotated[User, Depends(require_authenticated_user)]
UploaderUser = Annotated[User, Depends(require_uploader)]
AdminUser = Annotated[User, Depends(require_admin)]
