
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.mongodb import (
    connect_to_mongo,
    close_mongo_connection,
)


from app.api.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()

    yield

    await close_mongo_connection()


app = FastAPI(
    title="ADTU Notes API",
    description="Notes sharing platform backend",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def home():
    return {
        "message": "Welcome to ADTU Notes API"
    }


app.include_router(api_router, prefix="/api/v1")
