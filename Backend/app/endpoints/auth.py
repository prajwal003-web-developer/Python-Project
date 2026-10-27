from fastapi import APIRouter, Depends, status

from app.controllers.auth_controller import (
    register_user,
    login_user,
    check_auth,
    get_me,
    get_current_user,
)
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    MessageResponse,
)

auth = APIRouter(prefix="/auth", tags=["Authentication"])


@auth.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest):
    return await register_user(data)


@auth.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    return await login_user(data)


@auth.get("/check", response_model=MessageResponse)
async def check(current_user: dict = Depends(get_current_user)):
    return await check_auth(current_user)


@auth.get("/me", response_model=UserResponse)
async def me(current_user: dict = Depends(get_current_user)):
    return await get_me(current_user)