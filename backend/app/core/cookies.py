import re

from fastapi import Request, Response

from app.core.config import get_settings
from app.core.security import generate_csrf_token

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"
CSRF_COOKIE = "csrf_token"
CSRF_HEADER = "X-CSRF-Token"

_CSRF_SHAPE = re.compile(r"^[A-Za-z0-9_\-]{32,128}$")


def _common() -> dict:
    s = get_settings()
    return {"secure": s.use_secure_cookies, "samesite": s.cookie_samesite, "domain": s.cookie_domain}


def _refresh_path() -> str:
    return f"{get_settings().api_prefix}/auth"


def set_csrf_cookie(response: Response, csrf_token: str) -> None:
    s = get_settings()
    response.set_cookie(
        CSRF_COOKIE, csrf_token, max_age=s.refresh_token_expire_days * 86400,
        httponly=False, path="/", **_common(),
    )


def set_auth_cookies(response: Response, access: str, refresh: str, csrf_token: str) -> None:
    s = get_settings()
    response.set_cookie(
        ACCESS_COOKIE, access, max_age=s.access_token_expire_minutes * 60,
        httponly=True, path="/", **_common(),
    )
    # Refresh cookie is only ever sent to /api/auth/*
    response.set_cookie(
        REFRESH_COOKIE, refresh, max_age=s.refresh_token_expire_days * 86400,
        httponly=True, path=_refresh_path(), **_common(),
    )
    set_csrf_cookie(response, csrf_token)


def clear_auth_cookies(response: Response) -> None:
    c = _common()
    response.delete_cookie(ACCESS_COOKIE, path="/", httponly=True, **c)
    response.delete_cookie(REFRESH_COOKIE, path=_refresh_path(), httponly=True, **c)
    response.delete_cookie(CSRF_COOKIE, path="/", **c)


def current_or_new_csrf(request: Request) -> str:
    """Keep the browser's existing CSRF token stable across refreshes when it looks valid."""
    existing = request.cookies.get(CSRF_COOKIE)
    return existing if existing and _CSRF_SHAPE.match(existing) else generate_csrf_token()
