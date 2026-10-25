from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.cookies import ACCESS_COOKIE, CSRF_COOKIE, CSRF_HEADER, REFRESH_COOKIE
from app.core.security import tokens_match

SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


def _deny(message: str) -> JSONResponse:
    return JSONResponse(status_code=403, content={"error": {"code": "csrf_failed", "message": message}})


class CSRFMiddleware(BaseHTTPMiddleware):
    """Double-submit-cookie CSRF protection for cookie-authenticated, state-changing requests.

    The browser sends the `csrf_token` cookie automatically; the SPA must echo the same value in
    the `X-CSRF-Token` header (value is returned by /auth/login, /auth/refresh and /auth/csrf).
    An Origin allow-list check is applied as a second layer.
    """

    async def dispatch(self, request, call_next):
        if request.method in SAFE_METHODS:
            return await call_next(request)

        settings = get_settings()
        prefix = settings.api_prefix
        if request.url.path in {f"{prefix}/auth/login", f"{prefix}/auth/register"}:
            return await call_next(request)  # no session exists yet

        cookies = request.cookies
        if ACCESS_COOKIE in cookies or REFRESH_COOKIE in cookies:
            origin = request.headers.get("origin")
            if origin:
                own = f"{request.url.scheme}://{request.url.netloc}"
                if origin.rstrip("/") not in {*settings.cors_origins, own}:
                    return _deny("Origin not allowed")
            header = request.headers.get(CSRF_HEADER)
            cookie = cookies.get(CSRF_COOKIE)
            if not header or not cookie or not tokens_match(header, cookie):
                return _deny("Missing or invalid CSRF token")
        return await call_next(request)
