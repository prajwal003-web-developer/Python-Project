import time
from collections import deque

from fastapi import Request

from app.core.config import get_settings
from app.core.exceptions import RateLimitedError


def client_ip(request: Request) -> str:
    if get_settings().trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimiter:
    """In-memory sliding-window limiter, used as a FastAPI dependency.

    Per-process only. If you run several workers/instances, replace the storage with Redis.
    """

    def __init__(self, scope: str, limit_attr: str, window_attr: str):
        self.scope = scope
        self.limit_attr = limit_attr
        self.window_attr = window_attr
        self._hits: dict[str, deque[float]] = {}
        self._calls = 0

    async def __call__(self, request: Request) -> None:
        settings = get_settings()
        if not settings.rate_limit_enabled:
            return
        limit = getattr(settings, self.limit_attr)
        window = getattr(settings, self.window_attr)
        now = time.monotonic()
        key = f"{self.scope}:{client_ip(request)}"
        hits = self._hits.setdefault(key, deque())
        while hits and now - hits[0] > window:
            hits.popleft()
        if len(hits) >= limit:
            raise RateLimitedError(max(1, int(window - (now - hits[0])) + 1))
        hits.append(now)
        self._calls += 1
        if self._calls % 500 == 0:
            self._purge(now, window)

    def _purge(self, now: float, window: float) -> None:
        for key in [k for k, d in self._hits.items() if not d or now - d[-1] > window]:
            del self._hits[key]

    def reset(self) -> None:
        self._hits.clear()


login_limiter = RateLimiter("login", "login_rate_limit", "login_rate_window_seconds")
register_limiter = RateLimiter("register", "register_rate_limit", "register_rate_window_seconds")
refresh_limiter = RateLimiter("refresh", "refresh_rate_limit", "refresh_rate_window_seconds")
upload_limiter = RateLimiter("upload", "upload_rate_limit", "upload_rate_window_seconds")
department_request_limiter = RateLimiter(
    "dept_request", "department_request_rate_limit", "department_request_rate_window_seconds"
)
ALL_LIMITERS = (login_limiter, register_limiter, refresh_limiter, upload_limiter, department_request_limiter)
