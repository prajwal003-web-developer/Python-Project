
from datetime import datetime, timedelta, timezone

import jwt
from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from pymongo.errors import DuplicateKeyError

from app.db.mongodb import db, settings
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    MessageResponse,
)

password_hasher = PasswordHash.recommended()
bearer_scheme = HTTPBearer(auto_error=False)

users_collection = db["users"]


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hasher.verify(password, hashed_password)


def create_access_token(user_id: str) -> tuple[str, int]:
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    payload = {
        "sub": user_id,
        "exp": expires_at,
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return token, expires_in


def serialize_user(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "full_name": user["full_name"],
        "username": user["username"],
        "email": user["email"],
        "is_admin" : user.get("is_admin", False),
        "saved_notes": [
            str(note_id) for note_id in user.get("saved_notes", [])
        ],
    }


async def register_user(data: RegisterRequest):
    email = str(data.email).lower()
    username = data.username.strip().lower()

    print(data)

    existing_user = await users_collection.find_one({
        "$or": [
            {"email": email},
            {"username": username},
        ]
    })

    if existing_user:
        if existing_user["email"] == email:
            raise HTTPException(
                status_code=409,
                detail="Email is already registered",
            )

        raise HTTPException(
            status_code=409,
            detail="Username is already taken",
        )

    user_document = {
        "full_name": data.full_name.strip(),
        "username": username,
        "email": email,
        "hashed_password": hash_password(data.password),
        "saved_notes": [],
        "is_admin":False
    }

    try:
        result = await users_collection.insert_one(user_document)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=409,
            detail="Email or username is already registered",
        )

    return {
        "message": "Registration successful",
        "user_id": str(result.inserted_id),
    }


async def login_user(data: LoginRequest):
    email = str(data.email).lower()

    user = await users_collection.find_one({"email": email})

    if not user or not verify_password(
        data.password,
        user["hashed_password"],
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token, expires_in = create_access_token(str(user["_id"]))

    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        user_id = payload.get("sub")

        if not user_id or not ObjectId.is_valid(user_id):
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token",
            )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await users_collection.find_one({
        "_id": ObjectId(user_id)
    })

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User no longer exists",
        )

    return user


async def check_auth(
    current_user: dict = Depends(get_current_user),
):
    return MessageResponse(
        message="Authentication is valid",
        authenticated=True,
    )


async def get_me(
    current_user: dict = Depends(get_current_user),
):
    return serialize_user(current_user)


# Keep your existing get_current_user() function.

async def require_admin(
    current_user: dict = Depends(get_current_user),
):
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user
