from fastapi import APIRouter, Depends, Request, Response, status

from app.api.dependencies import CurrentUser, Database, csrf_doc_scheme
from app.core.cookies import (
    REFRESH_COOKIE, clear_auth_cookies, current_or_new_csrf, set_auth_cookies, set_csrf_cookie,
)
from app.core.exceptions import UnauthorizedError
from app.core.rate_limit import login_limiter, refresh_limiter, register_limiter
from app.schemas.auth import AuthResponse, CsrfResponse, LoginRequest, RegisterRequest
from app.schemas.common import MessageResponse
from app.schemas.user import ProfileUpdate, UserAccount, user_account
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserAccount, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(register_limiter)])
async def register(payload: RegisterRequest, db: Database):
    """Create an account. The role is always `user`; any submitted role is ignored."""
    return user_account(await auth_service.register_user(db, payload))


@router.post("/login", response_model=AuthResponse, dependencies=[Depends(login_limiter)])
async def login(payload: LoginRequest, request: Request, response: Response, db: Database):
    """Sets HttpOnly access/refresh cookies and returns the user plus the CSRF token."""
    user = await auth_service.authenticate(db, payload.email, payload.password)
    session = await auth_service.create_session(db, user, user_agent=request.headers.get("user-agent"))
    set_auth_cookies(response, session.access, session.refresh, session.csrf_token)
    return AuthResponse(user=user_account(user), csrf_token=session.csrf_token)


@router.post("/logout", response_model=MessageResponse, dependencies=[Depends(csrf_doc_scheme)])
async def logout(request: Request, response: Response, db: Database):
    """Revokes the refresh-token family and clears cookies. Works even with an expired access token."""
    await auth_service.revoke_session(db, request.cookies.get(REFRESH_COOKIE))
    clear_auth_cookies(response)
    return MessageResponse(message="Logged out")


@router.post("/refresh", response_model=AuthResponse, dependencies=[Depends(refresh_limiter), Depends(csrf_doc_scheme)])
async def refresh(request: Request, response: Response, db: Database):
    """Rotates the refresh token (single use) and issues a new short-lived access token."""
    token = request.cookies.get(REFRESH_COOKIE)
    try:
        if not token:
            raise UnauthorizedError("missing_refresh_token", "Refresh token missing")
        user, session = await auth_service.rotate_session(
            db, token, user_agent=request.headers.get("user-agent"), csrf_token=current_or_new_csrf(request)
        )
    except UnauthorizedError as exc:
        failure = exc.to_response()
        clear_auth_cookies(failure)
        return failure
    set_auth_cookies(response, session.access, session.refresh, session.csrf_token)
    return AuthResponse(user=user_account(user), csrf_token=session.csrf_token)


@router.get("/csrf", response_model=CsrfResponse)
async def csrf(request: Request, response: Response):
    """Returns (and if needed creates) the CSRF token; call after a page reload to restore it."""
    token = current_or_new_csrf(request)
    set_csrf_cookie(response, token)
    return CsrfResponse(csrf_token=token)


@router.get("/me", response_model=UserAccount)
async def me(user: CurrentUser):
    return user_account(user)


@router.patch("/me", response_model=UserAccount)
async def update_me(payload: ProfileUpdate, request: Request, response: Response, user: CurrentUser, db: Database):
    """Update name / username / password only. Role and status can never be changed here."""
    updated, password_changed = await auth_service.update_profile(db, user, payload)
    if password_changed:  # all sessions were revoked; keep this device signed in
        session = await auth_service.create_session(
            db, updated, user_agent=request.headers.get("user-agent"), csrf_token=current_or_new_csrf(request)
        )
        set_auth_cookies(response, session.access, session.refresh, session.csrf_token)
    return user_account(updated)
