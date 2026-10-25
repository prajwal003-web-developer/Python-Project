import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app")


class AppException(Exception):
    """Base class. Every error is rendered as {"error": {"code", "message", "details"?}}."""

    status_code = 500
    code = "internal_error"
    message = "Internal server error"

    def __init__(
        self,
        code: str | None = None,
        message: str | None = None,
        *,
        details: Any = None,
        headers: dict[str, str] | None = None,
    ):
        self.code = code or self.code
        self.message = message or self.message
        self.details = details
        self.headers = headers
        super().__init__(self.message)

    def to_response(self) -> JSONResponse:
        body: dict[str, Any] = {"error": {"code": self.code, "message": self.message}}
        if self.details:
            body["error"]["details"] = self.details
        return JSONResponse(status_code=self.status_code, content=body, headers=self.headers)


class BadRequestError(AppException):
    status_code, code, message = 400, "bad_request", "Bad request"


class UnauthorizedError(AppException):
    status_code, code, message = 401, "not_authenticated", "Authentication required"


class ForbiddenError(AppException):
    status_code, code, message = 403, "forbidden", "You do not have permission to perform this action"


class NotFoundError(AppException):
    status_code, code, message = 404, "not_found", "Resource not found"


class ConflictError(AppException):
    status_code, code, message = 409, "conflict", "Resource already exists"


class PayloadTooLargeError(AppException):
    status_code, code, message = 413, "file_too_large", "File is too large"


class UnsupportedMediaTypeError(AppException):
    status_code, code, message = 415, "unsupported_file_type", "Unsupported file type"


class UnprocessableError(AppException):
    status_code, code, message = 422, "unprocessable", "Request could not be processed"


class UpstreamError(AppException):
    status_code, code, message = 502, "upstream_error", "An upstream service failed"


class RateLimitedError(AppException):
    status_code, code = 429, "rate_limited"
    message = "Too many requests. Please try again later."

    def __init__(self, retry_after: int):
        super().__init__(headers={"Retry-After": str(retry_after)})


_HTTP_CODES = {
    401: "not_authenticated",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
}


def _validation_details(errors: list[dict[str, Any]]) -> list[dict[str, str]]:
    out = []
    for err in errors:
        loc = [str(p) for p in err.get("loc", ()) if p != "body"]
        msg = str(err.get("msg", "Invalid value")).removeprefix("Value error, ")
        out.append({"field": ".".join(loc), "message": msg})
    return out


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def _app_exc(_: Request, exc: AppException):
        return exc.to_response()

    @app.exception_handler(RequestValidationError)
    async def _validation_exc(_: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed",
                    "details": _validation_details(exc.errors()),
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_exc(_: Request, exc: StarletteHTTPException):
        code = _HTTP_CODES.get(exc.status_code, "http_error")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": code, "message": str(exc.detail)}},
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        # Log type + route only; never request bodies, cookies or secrets.
        logger.error("Unhandled %s on %s %s", type(exc).__name__, request.method, request.url.path, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_error", "message": "Internal server error"}},
        )
