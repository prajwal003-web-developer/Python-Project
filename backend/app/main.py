import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, auth, departments, faculties, notes, saved_notes, users
from app.core.config import get_settings
from app.core.cookies import CSRF_HEADER
from app.core.csrf import CSRFMiddleware
from app.core.exceptions import register_exception_handlers
from app.db.indexes import create_indexes
from app.db.mongodb import mongo

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    await mongo.connect(settings)
    await create_indexes(mongo.database)
    yield
    await mongo.close()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.enable_docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.enable_docs else None,
    )
    register_exception_handlers(app)

    # Added first => inner. CORS (added last) is outermost so even CSRF/403 responses get CORS headers.
    app.add_middleware(CSRFMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Accept", CSRF_HEADER],
        expose_headers=["Content-Disposition", "Retry-After"],
    )

    for router in (auth.router, faculties.router, departments.router, notes.router,
                   saved_notes.router, users.router, admin.router):
        app.include_router(router, prefix=settings.api_prefix)

    @app.get(f"{settings.api_prefix}/health", tags=["Health"])
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
